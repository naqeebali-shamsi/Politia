"""
Politia Data Ingestion Orchestrator
====================================
Imports election, affidavit, and activity data from raw CSV/JSON sources,
resolves entities across datasets, and computes accountability scores.

Idempotent: safe to run multiple times. Uses (name + constituency + year)
composite keys to detect duplicates before inserting.

Usage:
    python -m scripts.ingest
"""

from __future__ import annotations

import csv
import json
import logging
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so `app.*` imports resolve when running
# the script from the repo root via `python -m scripts.ingest`.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.config import get_settings
from app.domain.entities.activity import ActivityRecord
from app.domain.entities.constituency import Constituency
from app.domain.entities.disclosure import DisclosureRecord
from app.domain.entities.election import ElectionRecord
from app.domain.entities.politician import Politician
from app.domain.entities.score import ScoreRecord
from app.domain.entities.source import SourceRecord
from app.infrastructure.database.session import get_engine, get_session_factory, Base
from app.infrastructure.database.repositories.constituency_repository import SqlConstituencyRepository
from app.infrastructure.database.repositories.politician_repository import SqlPoliticianRepository
from app.infrastructure.database.repositories.election_repository import SqlElectionRepository
from app.infrastructure.database.repositories.disclosure_repository import SqlDisclosureRepository
from app.infrastructure.database.repositories.activity_repository import SqlActivityRepository
from app.infrastructure.database.repositories.score_repository import SqlScoreRepository
from app.infrastructure.database.repositories.source_repository import SqlSourceRepository
from app.infrastructure.ingestion.entity_resolver import normalize_name, match_names
from app.infrastructure.scoring.engine import ScoringEngine

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ingest")

# ---------------------------------------------------------------------------
# Data directory paths
# ---------------------------------------------------------------------------
DATA_ROOT = _PROJECT_ROOT / "data"
ELECTION_DIR = DATA_ROOT / "india-election-data" / "parliament-elections"
AFFIDAVIT_DIR = DATA_ROOT / "parliamentary-candidates-affidavit-data"
ACTIVITY_DIR = DATA_ROOT / "india-representatives-activity"


# ---------------------------------------------------------------------------
# Stats tracker
# ---------------------------------------------------------------------------
@dataclass
class PhaseStats:
    phase: str
    processed: int = 0
    created: int = 0
    skipped: int = 0
    errors: int = 0
    elapsed_sec: float = 0.0

    def summary(self) -> str:
        return (
            f"[{self.phase}] processed={self.processed} created={self.created} "
            f"skipped={self.skipped} errors={self.errors} "
            f"time={self.elapsed_sec:.1f}s"
        )


# ============================================================================
# PHASE 1 -- Election data (datameet parliament.csv)
# ============================================================================

def _read_parliament_csv(path: Path) -> list[dict]:
    """Read datameet parliament.csv. Columns: YEAR, STATE, PC, NAME, SEX, PARTY, AGE, CATEGORY, VOTES, ELECTORS, #"""
    rows: list[dict] = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def ingest_elections(session) -> PhaseStats:
    """
    Phase 1: Import parliament.csv into Constituency, Politician, and ElectionRecord tables.
    Deduplicates on (normalized_name, constituency, year).
    """
    stats = PhaseStats(phase="elections")
    t0 = time.monotonic()

    csv_path = ELECTION_DIR / "parliament.csv"
    if not csv_path.exists():
        logger.error("parliament.csv not found at %s", csv_path)
        stats.errors = 1
        stats.elapsed_sec = time.monotonic() - t0
        return stats

    raw_rows = _read_parliament_csv(csv_path)
    stats.processed = len(raw_rows)
    logger.info("Phase 1: loaded %d rows from parliament.csv", len(raw_rows))

    # Repositories
    const_repo = SqlConstituencyRepository(session)
    pol_repo = SqlPoliticianRepository(session)
    elec_repo = SqlElectionRepository(session)
    source_repo = SqlSourceRepository(session)

    # Register this file as a source (idempotent)
    source_url = f"file://{csv_path.as_posix()}"
    source = source_repo.get_by_url(source_url)
    if source is None:
        source = source_repo.create(SourceRecord(
            source_name="datameet_elections",
            url=source_url,
            content_type="csv",
            fetch_timestamp=datetime.now(timezone.utc),
            parse_status="completed",
        ))

    # ----- In-memory caches to avoid repeated DB lookups -----
    # constituency cache: (upper_name, upper_state) -> Constituency entity
    constituency_cache: dict[tuple[str, str], Constituency] = {}
    # politician cache: (normalized_name, upper_constituency) -> Politician entity
    politician_cache: dict[tuple[str, str], Politician] = {}
    # election dedup: (politician_id, year) set -- within a single constituency a
    # candidate appears only once per year, but they may contest from different
    # constituencies across years.
    election_seen: set[tuple[int, int, int | None]] = set()

    # Pre-load existing constituencies
    _existing_const = const_repo.get_all(offset=0, limit=100_000)
    for c in _existing_const:
        constituency_cache[(c.name.upper(), c.state.upper())] = c

    # Pre-load existing politicians
    _existing_pols = pol_repo.get_all(offset=0, limit=500_000)
    for p in _existing_pols:
        norm = normalize_name(p.full_name)
        const_key = (p.current_constituency or "").upper()
        politician_cache[(norm, const_key)] = p

    # Pre-load existing election records for dedup
    _existing_elecs = elec_repo.get_all(offset=0, limit=1_000_000)
    for e in _existing_elecs:
        election_seen.add((e.politician_id, e.election_year, e.constituency_id))

    # Batch accumulators
    new_elections: list[ElectionRecord] = []
    BATCH_SIZE = 2000

    def flush_elections():
        nonlocal new_elections
        if new_elections:
            elec_repo.bulk_create(new_elections)
            stats.created += len(new_elections)
            new_elections = []

    for idx, row in enumerate(raw_rows):
        try:
            name_raw = (row.get("NAME") or "").strip()
            party = (row.get("PARTY") or "").strip()
            constituency_name = (row.get("PC") or "").strip()
            state = (row.get("STATE") or "").strip()
            sex = (row.get("SEX") or "").strip()
            category = (row.get("CATEGORY") or "").strip()

            year_str = (row.get("YEAR") or "0").strip()
            year = int(year_str) if year_str.isdigit() else 0
            votes_str = (row.get("VOTES") or "0").strip()
            votes = int(votes_str) if votes_str.isdigit() else 0
            position_str = (row.get("#") or "0").strip()
            position = int(position_str) if position_str.isdigit() else 99
            result = "Won" if position == 1 else "Lost"

            if not name_raw or not constituency_name or year == 0:
                stats.skipped += 1
                continue

            # --- Constituency (get or create) ---
            const_key = (constituency_name.upper(), state.upper())
            if const_key not in constituency_cache:
                existing = const_repo.get_by_name_and_state(constituency_name.upper(), state.upper())
                if existing:
                    constituency_cache[const_key] = existing
                else:
                    new_const = const_repo.create(Constituency(
                        name=constituency_name.upper(),
                        state=state.upper(),
                        chamber="Lok Sabha",
                        constituency_type=category if category in ("GEN", "SC", "ST") else None,
                    ))
                    constituency_cache[const_key] = new_const

            constituency = constituency_cache[const_key]

            # --- Politician (entity-resolve or create) ---
            norm_name = normalize_name(name_raw)
            pol_key = (norm_name, constituency_name.upper())

            if pol_key not in politician_cache:
                # Try fuzzy match against existing DB politicians with same constituency
                existing_matches = pol_repo.get_by_name(name_raw)
                matched = None
                for em in existing_matches:
                    if match_names(name_raw, em.full_name) >= 85.0:
                        matched = em
                        break

                if matched is None:
                    new_pol = pol_repo.create(Politician(
                        full_name=name_raw.upper(),
                        name_variants=[name_raw],
                        gender=_map_gender(sex),
                        current_party=party,
                        current_chamber="Lok Sabha",
                        current_constituency=constituency_name.upper(),
                        current_state=state.upper(),
                        is_active=(result == "Won"),
                    ))
                    politician_cache[pol_key] = new_pol
                else:
                    politician_cache[pol_key] = matched
                    # Update denormalized fields to latest election
                    if year >= (matched.last_updated.year if matched.last_updated else 0):
                        matched.current_party = party
                        matched.current_state = state.upper()
                        matched.current_constituency = constituency_name.upper()
                        if result == "Won":
                            matched.is_active = True
                        pol_repo.update(matched)

            politician = politician_cache[pol_key]

            # --- Election record (idempotent) ---
            dedup_key = (politician.id, year, constituency.id)
            if dedup_key in election_seen:
                stats.skipped += 1
                continue

            election_seen.add(dedup_key)
            new_elections.append(ElectionRecord(
                politician_id=politician.id,
                constituency_id=constituency.id,
                election_year=year,
                election_type="General",
                party=party,
                result=result,
                votes=votes if votes > 0 else None,
                source_id=source.id,
            ))

            if len(new_elections) >= BATCH_SIZE:
                flush_elections()

        except Exception as exc:
            stats.errors += 1
            if stats.errors <= 20:
                logger.warning("Phase 1 row %d error: %s", idx, exc)

    flush_elections()
    session.commit()

    stats.elapsed_sec = time.monotonic() - t0
    logger.info(stats.summary())
    return stats


def _map_gender(sex_code: str) -> str | None:
    code = sex_code.strip().upper()
    if code in ("M", "MALE"):
        return "Male"
    if code in ("F", "FEMALE"):
        return "Female"
    return None


# ============================================================================
# PHASE 2 -- Affidavit data (bkamapantula CSVs)
# ============================================================================

def ingest_affidavits(session) -> PhaseStats:
    """
    Phase 2: Import affidavit disclosure data. Match to existing politicians
    via entity resolution on (name, constituency, year).
    Creates DisclosureRecord entries.
    """
    stats = PhaseStats(phase="affidavits")
    t0 = time.monotonic()

    csv_path = AFFIDAVIT_DIR / "2004-2019-affidavits.csv"
    if not csv_path.exists():
        logger.error("Affidavit CSV not found at %s", csv_path)
        stats.errors = 1
        stats.elapsed_sec = time.monotonic() - t0
        return stats

    raw_rows: list[dict] = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_rows.append(row)

    stats.processed = len(raw_rows)
    logger.info("Phase 2: loaded %d rows from affidavit CSV", len(raw_rows))

    pol_repo = SqlPoliticianRepository(session)
    disc_repo = SqlDisclosureRepository(session)
    source_repo = SqlSourceRepository(session)

    # Source record
    source_url = f"file://{csv_path.as_posix()}"
    source = source_repo.get_by_url(source_url)
    if source is None:
        source = source_repo.create(SourceRecord(
            source_name="affidavit_csv",
            url=source_url,
            content_type="csv",
            fetch_timestamp=datetime.now(timezone.utc),
            parse_status="completed",
        ))

    # Build politician lookup index: (normalized_name, upper_constituency) -> Politician
    all_politicians = pol_repo.get_all(offset=0, limit=500_000)
    pol_index: dict[tuple[str, str], Politician] = {}
    for p in all_politicians:
        norm = normalize_name(p.full_name)
        const = (p.current_constituency or "").upper()
        pol_index[(norm, const)] = p

    # Dedup: (politician_id, year)
    existing_disclosures: set[tuple[int, int]] = set()
    _all_disc = disc_repo.get_all(offset=0, limit=1_000_000)
    for d in _all_disc:
        existing_disclosures.add((d.politician_id, d.election_year))

    new_disclosures: list[DisclosureRecord] = []
    unmatched = 0

    for idx, row in enumerate(raw_rows):
        try:
            name_raw = (row.get("Candidate") or "").strip()
            constituency = (row.get("Constituency") or "").strip().upper()
            state = (row.get("State") or "").strip().upper()
            year = int(row.get("Year") or 0)

            if not name_raw or year == 0:
                stats.skipped += 1
                continue

            norm = normalize_name(name_raw)

            # Try exact key match first
            politician = pol_index.get((norm, constituency))

            # Fall back to fuzzy match across all politicians
            if politician is None:
                best_score = 0.0
                best_match = None
                for (pn, pc), p in pol_index.items():
                    if pc != constituency:
                        continue
                    score = match_names(name_raw, p.full_name)
                    if score > best_score:
                        best_score = score
                        best_match = p
                if best_score >= 80.0:
                    politician = best_match

            if politician is None:
                unmatched += 1
                stats.skipped += 1
                continue

            # Idempotency check
            if (politician.id, year) in existing_disclosures:
                stats.skipped += 1
                continue
            existing_disclosures.add((politician.id, year))

            criminal_cases = _safe_int(row.get("CriminalCases"))
            total_assets = _safe_float(row.get("TotalAssets"))
            total_liabilities = _safe_float(row.get("TotalLiabilities"))

            new_disclosures.append(DisclosureRecord(
                politician_id=politician.id,
                election_year=year,
                total_assets=total_assets,
                total_liabilities=total_liabilities,
                criminal_cases=criminal_cases,
                affidavit_complete=total_assets is not None,
                source_id=source.id,
            ))

            # Also update politician education if available
            education = (row.get("Education") or "").strip()
            if education and not politician.education:
                politician.education = education
                pol_repo.update(politician)

        except Exception as exc:
            stats.errors += 1
            if stats.errors <= 20:
                logger.warning("Phase 2 row %d error: %s", idx, exc)

    if new_disclosures:
        # Bulk create in chunks
        for i in range(0, len(new_disclosures), 2000):
            chunk = new_disclosures[i:i + 2000]
            disc_repo.bulk_create(chunk)
        stats.created = len(new_disclosures)

    session.commit()

    logger.info("Phase 2: %d unmatched candidates (no politician record)", unmatched)
    stats.elapsed_sec = time.monotonic() - t0
    logger.info(stats.summary())
    return stats


# ============================================================================
# PHASE 3 -- PRS Activity data (Vonter CSV per Lok Sabha term)
# ============================================================================

def ingest_activity(session) -> PhaseStats:
    """
    Phase 3: Import PRS parliamentary activity data from per-term CSVs.
    Files are semicolon-delimited. Key columns: Name, Constituency, Attendance,
    Debates, Questions, Private Member Bills, State, Party, Lok Sabha.
    """
    stats = PhaseStats(phase="activity")
    t0 = time.monotonic()

    # Look for per-term CSVs first (more structured), then the combined file
    csv_dir = ACTIVITY_DIR / "csv" / "Lok Sabha"
    combined_csv = ACTIVITY_DIR / "csv" / "Lok Sabha.csv"

    term_files: list[Path] = []
    if csv_dir.exists():
        term_files = sorted(csv_dir.glob("*.csv"))
    if not term_files and combined_csv.exists():
        term_files = [combined_csv]

    if not term_files:
        logger.warning("Phase 3: no activity CSV files found in %s", ACTIVITY_DIR)
        stats.elapsed_sec = time.monotonic() - t0
        return stats

    pol_repo = SqlPoliticianRepository(session)
    act_repo = SqlActivityRepository(session)
    source_repo = SqlSourceRepository(session)

    # Build politician lookup
    all_politicians = pol_repo.get_all(offset=0, limit=500_000)
    pol_by_name: dict[str, list[Politician]] = {}
    for p in all_politicians:
        norm = normalize_name(p.full_name)
        pol_by_name.setdefault(norm, []).append(p)

    # Dedup: (politician_id, term_number)
    existing_activities: set[tuple[int, int | None]] = set()
    _all_acts = act_repo.get_all(offset=0, limit=500_000)
    for a in _all_acts:
        existing_activities.add((a.politician_id, a.term_number))

    total_unmatched = 0

    for csv_path in term_files:
        logger.info("Phase 3: processing %s", csv_path.name)

        source_url = f"file://{csv_path.as_posix()}"
        source = source_repo.get_by_url(source_url)
        if source is None:
            source = source_repo.create(SourceRecord(
                source_name="vonter_activity",
                url=source_url,
                content_type="csv",
                fetch_timestamp=datetime.now(timezone.utc),
                parse_status="completed",
            ))

        rows: list[dict] = []
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            # These files use semicolon delimiter
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                rows.append(row)

        stats.processed += len(rows)
        new_activities: list[ActivityRecord] = []

        for idx, row in enumerate(rows):
            try:
                name_raw = (row.get("Name") or "").strip().strip('"')
                constituency = (row.get("Constituency") or "").strip().strip('"')
                state = (row.get("State") or "").strip().strip('"')
                party = (row.get("Party") or "").strip().strip('"')
                lok_sabha = (row.get("Lok Sabha") or "").strip().strip('"')

                # Parse term number from "15th", "16th", etc.
                term_number = _parse_term_number(lok_sabha)

                attendance_raw = (row.get("Attendance") or "0").strip().strip('"').replace("%", "")
                attendance = _safe_float(attendance_raw)

                debates = _safe_int((row.get("Debates") or "0").strip().strip('"'))
                questions = _safe_int((row.get("Questions") or "0").strip().strip('"'))
                private_bills = _safe_int(
                    (row.get("Private Member Bills") or "0").strip().strip('"')
                )

                if not name_raw:
                    stats.skipped += 1
                    continue

                # Entity resolution
                norm = normalize_name(name_raw)
                politician = _resolve_politician(
                    norm, name_raw, constituency.upper(), pol_by_name
                )

                if politician is None:
                    total_unmatched += 1
                    stats.skipped += 1
                    continue

                # Idempotency
                if (politician.id, term_number) in existing_activities:
                    stats.skipped += 1
                    continue
                existing_activities.add((politician.id, term_number))

                new_activities.append(ActivityRecord(
                    politician_id=politician.id,
                    term_number=term_number,
                    session_name=f"{lok_sabha} Lok Sabha" if lok_sabha else None,
                    attendance_percentage=attendance,
                    questions_asked=questions,
                    debates_participated=debates,
                    private_bills_introduced=private_bills,
                    source_id=source.id,
                ))

            except Exception as exc:
                stats.errors += 1
                if stats.errors <= 20:
                    logger.warning("Phase 3 row %d in %s error: %s", idx, csv_path.name, exc)

        if new_activities:
            for i in range(0, len(new_activities), 2000):
                chunk = new_activities[i:i + 2000]
                act_repo.bulk_create(chunk)
            stats.created += len(new_activities)

    session.commit()

    logger.info("Phase 3: %d unmatched MPs (no politician record)", total_unmatched)
    stats.elapsed_sec = time.monotonic() - t0
    logger.info(stats.summary())
    return stats


def _resolve_politician(
    norm_name: str,
    raw_name: str,
    constituency_upper: str,
    pol_by_name: dict[str, list[Politician]],
) -> Politician | None:
    """Resolve a name to a Politician using the in-memory index."""
    # Exact normalized name match
    candidates = pol_by_name.get(norm_name, [])
    if len(candidates) == 1:
        return candidates[0]

    # If multiple matches, narrow by constituency
    if len(candidates) > 1:
        for c in candidates:
            if (c.current_constituency or "").upper() == constituency_upper:
                return c
        # Return first match if constituency doesn't narrow it
        return candidates[0]

    # Fuzzy match across all names
    best_score = 0.0
    best_match = None
    for pn, pols in pol_by_name.items():
        score = match_names(raw_name, pols[0].full_name)
        if score > best_score:
            best_score = score
            best_match = pols[0]
            # If we also match constituency, prefer that strongly
            for p in pols:
                if (p.current_constituency or "").upper() == constituency_upper:
                    if score >= 75.0:
                        return p

    if best_score >= 82.0 and best_match is not None:
        return best_match

    return None


def _parse_term_number(lok_sabha_str: str) -> int | None:
    """Parse '15th' -> 15, '16th' -> 16, etc."""
    s = lok_sabha_str.strip().lower()
    num_part = ""
    for ch in s:
        if ch.isdigit():
            num_part += ch
        else:
            break
    return int(num_part) if num_part else None


# ============================================================================
# PHASE 4 -- Scoring
# ============================================================================

def compute_scores(session) -> PhaseStats:
    """
    Phase 4: Compute accountability scores for all politicians who have at
    least one activity or disclosure record.
    """
    stats = PhaseStats(phase="scoring")
    t0 = time.monotonic()

    pol_repo = SqlPoliticianRepository(session)
    act_repo = SqlActivityRepository(session)
    disc_repo = SqlDisclosureRepository(session)
    elec_repo = SqlElectionRepository(session)
    score_repo = SqlScoreRepository(session)

    engine = ScoringEngine()

    all_politicians = pol_repo.get_all(offset=0, limit=500_000)
    stats.processed = len(all_politicians)
    logger.info("Phase 4: computing scores for %d politicians", len(all_politicians))

    # Get chamber-wide baselines for normalization
    baselines = act_repo.get_chamber_averages()
    logger.info("Phase 4: baselines = %s", baselines)

    # Invalidate all current scores so we can re-compute (batch to avoid SQLite parameter limits)
    all_ids = [p.id for p in all_politicians if p.id is not None]
    invalidated = 0
    for i in range(0, len(all_ids), 500):
        chunk = all_ids[i:i + 500]
        invalidated += score_repo.invalidate_current_scores(chunk)
    if invalidated:
        logger.info("Phase 4: invalidated %d existing current scores", invalidated)

    new_scores: list[ScoreRecord] = []

    for politician in all_politicians:
        if politician.id is None:
            continue
        try:
            # Gather activity data (use latest term)
            activities = act_repo.get_by_politician(politician.id)
            participation_data: dict[str, Any] = {}
            if activities:
                # Use the most recent activity record
                latest = activities[0]  # already ordered or we take first
                participation_data = {
                    "attendance_percentage": latest.attendance_percentage,
                    "questions_asked": latest.questions_asked,
                    "debates_participated": latest.debates_participated,
                    "committee_memberships": latest.committee_memberships,
                }

            # Gather disclosure data
            latest_disc = disc_repo.get_latest_by_politician(politician.id)
            disclosure_data: dict[str, Any] = {}
            if latest_disc:
                disclosure_data = {
                    "affidavit_complete": latest_disc.affidavit_complete,
                    "total_assets": latest_disc.total_assets,
                    "total_liabilities": latest_disc.total_liabilities,
                    "pan_declared": latest_disc.pan_declared,
                }

            # Count election records for disclosure linkage score
            elections = elec_repo.get_by_politician(politician.id)
            disclosure_data["election_count"] = len(elections)

            # Gather integrity data
            integrity_data: dict[str, Any] = {}
            if latest_disc:
                integrity_data = {
                    "criminal_cases": latest_disc.criminal_cases,
                    "serious_criminal_cases": latest_disc.serious_criminal_cases,
                }

            score = engine.compute_score(
                politician_id=politician.id,
                participation_data=participation_data,
                disclosure_data=disclosure_data,
                integrity_data=integrity_data,
                baselines=baselines,
            )

            new_scores.append(score)

        except Exception as exc:
            stats.errors += 1
            if stats.errors <= 20:
                logger.warning(
                    "Phase 4: scoring failed for politician %d (%s): %s",
                    politician.id, politician.full_name, exc,
                )

    if new_scores:
        for i in range(0, len(new_scores), 2000):
            chunk = new_scores[i:i + 2000]
            score_repo.bulk_create(chunk)
        stats.created = len(new_scores)

    session.commit()

    stats.elapsed_sec = time.monotonic() - t0
    logger.info(stats.summary())
    return stats


# ============================================================================
# Utility helpers
# ============================================================================

def _safe_int(value: Any) -> int:
    """Parse an integer from a possibly messy string. Returns 0 on failure."""
    if value is None:
        return 0
    try:
        cleaned = str(value).replace(",", "").replace('"', "").strip()
        if not cleaned or cleaned.upper() in ("NA", "N/A", "NONE", "-"):
            return 0
        return int(float(cleaned))
    except (ValueError, TypeError):
        return 0


def _safe_float(value: Any) -> float | None:
    """Parse a float from a possibly messy string. Returns None on failure."""
    if value is None:
        return None
    try:
        cleaned = str(value).replace(",", "").replace('"', "").replace("Rs", "").replace("~", "").strip()
        if not cleaned or cleaned.upper() in ("NA", "N/A", "NONE", "-"):
            return None
        return float(cleaned)
    except (ValueError, TypeError):
        return None


# ============================================================================
# Main orchestrator
# ============================================================================

def main():
    logger.info("=" * 60)
    logger.info("Politia Data Ingestion Pipeline")
    logger.info("=" * 60)

    settings = get_settings()
    logger.info("Database: %s", settings.database_url.split("@")[-1] if "@" in settings.database_url else settings.database_url)

    # Ensure tables exist
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified / created")

    session_factory = get_session_factory()
    session = session_factory()

    all_stats: list[PhaseStats] = []
    pipeline_start = time.monotonic()

    try:
        # Phase 1: Elections
        logger.info("-" * 40)
        logger.info("PHASE 1: Election Data (datameet)")
        logger.info("-" * 40)
        s1 = ingest_elections(session)
        all_stats.append(s1)

        # Phase 2: Affidavits
        logger.info("-" * 40)
        logger.info("PHASE 2: Affidavit Data (bkamapantula)")
        logger.info("-" * 40)
        s2 = ingest_affidavits(session)
        all_stats.append(s2)

        # Phase 3: Activity
        logger.info("-" * 40)
        logger.info("PHASE 3: Activity Data (Vonter/PRS)")
        logger.info("-" * 40)
        s3 = ingest_activity(session)
        all_stats.append(s3)

        # Phase 4: Scoring
        logger.info("-" * 40)
        logger.info("PHASE 4: Score Computation")
        logger.info("-" * 40)
        s4 = compute_scores(session)
        all_stats.append(s4)

    except Exception as exc:
        logger.error("Pipeline failed: %s", exc, exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()

    # Final summary
    total_elapsed = time.monotonic() - pipeline_start
    logger.info("=" * 60)
    logger.info("INGESTION COMPLETE -- %.1f seconds total", total_elapsed)
    logger.info("=" * 60)
    for s in all_stats:
        logger.info("  %s", s.summary())

    total_errors = sum(s.errors for s in all_stats)
    total_created = sum(s.created for s in all_stats)
    logger.info("  TOTAL: %d records created, %d errors", total_created, total_errors)

    if total_errors > 0:
        logger.warning("Pipeline completed with %d errors -- review logs above", total_errors)
        sys.exit(1)
    else:
        logger.info("Pipeline completed successfully")


if __name__ == "__main__":
    main()
