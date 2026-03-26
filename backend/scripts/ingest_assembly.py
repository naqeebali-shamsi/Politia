"""
Ingest ~398K state assembly (Vidhan Sabha) election records from datameet.
Uses bulk SQL inserts for speed and entity resolution for politician matching.

Usage:
    POLITIA_DATABASE_URL="sqlite:///./politia_dev.db" python scripts/ingest_assembly.py
"""
import csv
import sys
import time
import logging
from pathlib import Path
from collections import defaultdict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.config import get_settings
from app.infrastructure.database.session import get_engine, Base
import app.infrastructure.database.models  # noqa: F401 — register models with Base
from app.infrastructure.ingestion.entity_resolver import (
    normalize_name, clean_name_for_storage, normalize_state,
    is_common_name,
)
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ingest_assembly")

DATA_ROOT = _PROJECT_ROOT / "data"
CHAMBER = "Vidhan Sabha"
BATCH_SIZE = 1000


def read_assembly_csv(path: Path) -> list[dict]:
    """
    Read datameet assembly.csv.
    Columns: ST_NAME, YEAR, AC_NO, #, AC_NAME, AC_TYPE, NAME, SEX, AGE, CATEGORY, PARTY, VOTES
    """
    rows = []
    with open(path, newline="", encoding="latin-1") as f:
        for row in csv.DictReader(f):
            name_raw = (row.get("NAME") or "").strip()
            if not name_raw:
                continue

            state_raw = (row.get("ST_NAME") or "").strip()
            ac_name = (row.get("AC_NAME") or "").strip().upper()
            if not ac_name or not state_raw:
                continue

            year_str = (row.get("YEAR") or "0").strip()
            year = int(year_str) if year_str.isdigit() else 0
            if year == 0:
                continue

            votes_str = (row.get("VOTES") or "0").strip()
            votes = int(votes_str) if votes_str.isdigit() else 0

            pos_str = (row.get("#") or "99").strip()
            position = int(pos_str) if pos_str.isdigit() else 99

            sex = (row.get("SEX") or "").strip().upper()
            party = (row.get("PARTY") or "").strip()
            ac_type = (row.get("AC_TYPE") or "").strip().upper()

            rows.append({
                "year": year,
                "name": clean_name_for_storage(name_raw),
                "state": normalize_state(state_raw.upper()),
                "constituency": ac_name,
                "constituency_type": ac_type if ac_type in ("GEN", "SC", "ST") else None,
                "party": party,
                "votes": votes,
                "position": position,
                "sex": sex,
            })

    return rows


def determine_winners(rows: list[dict]) -> list[dict]:
    """
    Determine winners: candidate with most votes per constituency per year.
    The '#' column from CSV is position, but we recompute from votes for reliability.
    """
    by_seat = defaultdict(list)
    for r in rows:
        key = (r["year"], r["state"], r["constituency"])
        by_seat[key].append(r)

    for key, candidates in by_seat.items():
        candidates.sort(key=lambda c: c["votes"], reverse=True)
        for i, c in enumerate(candidates):
            c["position"] = i + 1

    return rows


def main():
    settings = get_settings()
    logger.info(f"Database: {settings.database_url[:50]}...")

    engine = get_engine()

    # For SQLite dev: drop old unique index if it exists without chamber,
    # then let create_all build the new schema
    if settings.database_url.startswith("sqlite"):
        with engine.begin() as conn:
            try:
                conn.execute(text("DROP INDEX IF EXISTS ix_constituency_name_state"))
            except Exception:
                pass

    Base.metadata.create_all(bind=engine)
    logger.info("Tables created/verified")

    t0 = time.monotonic()

    # ==================== LOAD CSV ====================
    csv_path = DATA_ROOT / "india-election-data" / "assembly-elections" / "assembly.csv"
    if not csv_path.exists():
        logger.error(f"CSV not found: {csv_path}")
        return

    logger.info(f"Reading {csv_path}...")
    all_rows = read_assembly_csv(csv_path)
    logger.info(f"Loaded {len(all_rows)} valid rows from CSV")

    # Recompute winners from votes
    all_rows = determine_winners(all_rows)
    logger.info("Winners determined by vote count")

    # ==================== LOAD EXISTING DATA ====================
    logger.info("Loading existing DB data for idempotency...")
    with engine.connect() as conn:
        # Existing Vidhan Sabha constituencies: (name, state) -> id
        existing_constituencies = {}
        for r in conn.execute(
            text("SELECT id, name, state FROM constituencies WHERE chamber = :ch"),
            {"ch": CHAMBER},
        ).fetchall():
            existing_constituencies[(r[1], r[2])] = r[0]

        # Existing politicians: (normalized_name, constituency, state) -> id
        existing_politicians = {}
        for r in conn.execute(
            text("SELECT id, full_name, current_constituency, current_state FROM politicians")
        ).fetchall():
            norm = normalize_name(r[1])
            state = normalize_state(r[3] or "")
            existing_politicians[(norm, r[2] or "", state)] = r[0]

        # Existing assembly elections: (politician_id, year, constituency_id) for dedup
        existing_elections = set()
        for r in conn.execute(
            text("""
                SELECT er.politician_id, er.election_year, er.constituency_id
                FROM election_records er
                JOIN constituencies c ON c.id = er.constituency_id
                WHERE c.chamber = :ch
            """),
            {"ch": CHAMBER},
        ).fetchall():
            existing_elections.add((r[0], r[1], r[2]))

        max_pol_id = conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM politicians")).scalar()
        max_const_id = conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM constituencies")).scalar()

    logger.info(
        f"  Existing: {len(existing_constituencies)} VS constituencies, "
        f"{len(existing_politicians)} politicians, {len(existing_elections)} VS elections"
    )

    # Build a fast lookup index: (normalized_name, state) -> pol_id
    # This avoids O(n) scans for cross-constituency matching
    name_state_index = {}  # (norm_name, state) -> pol_id
    for (pn, pc, ps), pid in existing_politicians.items():
        ns_key = (pn, ps)
        if ns_key not in name_state_index:
            name_state_index[ns_key] = pid

    # ==================== BUILD INSERTS ====================
    logger.info("Building insert batches...")

    new_constituencies = []
    new_politicians = []
    new_elections = []
    next_const_id = max_const_id + 1
    next_pol_id = max_pol_id + 1

    stats = {
        "const_created": 0,
        "const_reused": 0,
        "pol_created": 0,
        "pol_matched": 0,
        "elec_created": 0,
        "elec_skipped": 0,
        "rows_skipped": 0,
    }

    for row in all_rows:
        name = row["name"]
        constituency = row["constituency"]
        state = row["state"]
        year = row["year"]
        party = row["party"]
        votes = row["votes"]
        position = row["position"]
        sex = row["sex"]

        # --- Constituency: get or create ---
        const_key = (constituency, state)
        if const_key not in existing_constituencies:
            existing_constituencies[const_key] = next_const_id
            ct = row.get("constituency_type")
            new_constituencies.append({
                "id": next_const_id,
                "name": constituency,
                "state": state,
                "chamber": CHAMBER,
                "constituency_type": ct,
            })
            next_const_id += 1
            stats["const_created"] += 1
        else:
            stats["const_reused"] += 1
        const_id = existing_constituencies[const_key]

        # --- Politician: match or create ---
        norm = normalize_name(name)
        if not norm:
            stats["rows_skipped"] += 1
            continue

        # Primary key: exact name + constituency + state
        pol_key = (norm, constituency, state)
        pol_id = existing_politicians.get(pol_key)

        if pol_id is None:
            # For uncommon names, try O(1) lookup by (name, state)
            if not is_common_name(name):
                ns_key = (norm, state)
                matched_id = name_state_index.get(ns_key)
                if matched_id:
                    pol_id = matched_id
                    existing_politicians[pol_key] = pol_id
                    stats["pol_matched"] += 1

        if pol_id is None:
            pol_id = next_pol_id
            existing_politicians[pol_key] = pol_id
            gender = None
            if sex in ("M", "MALE"):
                gender = "Male"
            elif sex in ("F", "FEMALE"):
                gender = "Female"

            new_politicians.append({
                "id": pol_id,
                "full_name": name,
                "current_party": party,
                "current_state": state,
                "current_constituency": constituency,
                "current_chamber": CHAMBER,
                "gender": gender,
                "is_active": position == 1,
            })
            # Update name_state_index for future rows
            ns_key = (norm, state)
            if ns_key not in name_state_index:
                name_state_index[ns_key] = pol_id
            next_pol_id += 1
            stats["pol_created"] += 1

        # --- Election record: dedup ---
        dedup_key = (pol_id, year, const_id)
        if dedup_key in existing_elections:
            stats["elec_skipped"] += 1
            continue
        existing_elections.add(dedup_key)

        new_elections.append({
            "politician_id": pol_id,
            "constituency_id": const_id,
            "election_year": year,
            "election_type": "General",
            "party": party,
            "result": "Won" if position == 1 else "Lost",
            "votes": votes if votes > 0 else None,
        })
        stats["elec_created"] += 1

    logger.info(
        f"Prepared: {stats['const_created']} new constituencies, "
        f"{stats['pol_created']} new politicians, "
        f"{stats['elec_created']} new elections"
    )
    logger.info(
        f"Matched {stats['pol_matched']} politicians to existing, "
        f"skipped {stats['elec_skipped']} duplicate elections, "
        f"{stats['rows_skipped']} rows with empty names"
    )

    # ==================== BULK INSERT ====================
    logger.info("Inserting into database...")
    t_insert = time.monotonic()

    with engine.begin() as conn:
        # Constituencies
        if new_constituencies:
            for i in range(0, len(new_constituencies), BATCH_SIZE):
                batch = new_constituencies[i : i + BATCH_SIZE]
                conn.execute(
                    text("""
                        INSERT INTO constituencies (id, name, state, chamber, constituency_type)
                        VALUES (:id, :name, :state, :chamber, :constituency_type)
                    """),
                    batch,
                )
            logger.info(f"  Inserted {len(new_constituencies)} constituencies")

        # Politicians
        if new_politicians:
            for i in range(0, len(new_politicians), BATCH_SIZE):
                batch = new_politicians[i : i + BATCH_SIZE]
                conn.execute(
                    text("""
                        INSERT INTO politicians (id, full_name, current_party, current_state,
                            current_constituency, current_chamber, gender, is_active)
                        VALUES (:id, :full_name, :current_party, :current_state,
                            :current_constituency, :current_chamber, :gender, :is_active)
                    """),
                    batch,
                )
            logger.info(f"  Inserted {len(new_politicians)} politicians")

        # Election records
        if new_elections:
            for i in range(0, len(new_elections), BATCH_SIZE):
                batch = new_elections[i : i + BATCH_SIZE]
                conn.execute(
                    text("""
                        INSERT INTO election_records (politician_id, constituency_id,
                            election_year, election_type, party, result, votes)
                        VALUES (:politician_id, :constituency_id,
                            :election_year, :election_type, :party, :result, :votes)
                    """),
                    batch,
                )
            logger.info(f"  Inserted {len(new_elections)} election records")

    insert_time = time.monotonic() - t_insert
    logger.info(f"  Insert phase: {insert_time:.1f}s")

    # ==================== STATS ====================
    total_time = time.monotonic() - t0
    logger.info("=" * 60)
    logger.info(f"ASSEMBLY INGESTION COMPLETE in {total_time:.1f}s")
    logger.info(f"  Constituencies created: {stats['const_created']}")
    logger.info(f"  Constituencies reused:  {stats['const_reused']}")
    logger.info(f"  Politicians created:    {stats['pol_created']}")
    logger.info(f"  Politicians matched:    {stats['pol_matched']}")
    logger.info(f"  Elections created:      {stats['elec_created']}")
    logger.info(f"  Elections skipped:      {stats['elec_skipped']}")

    # Validation queries
    with engine.connect() as conn:
        vs_const = conn.execute(
            text("SELECT COUNT(*) FROM constituencies WHERE chamber = :ch"),
            {"ch": CHAMBER},
        ).scalar()
        vs_elec = conn.execute(
            text("""
                SELECT COUNT(*) FROM election_records er
                JOIN constituencies c ON c.id = er.constituency_id
                WHERE c.chamber = :ch
            """),
            {"ch": CHAMBER},
        ).scalar()
        vs_winners = conn.execute(
            text("""
                SELECT COUNT(*) FROM election_records er
                JOIN constituencies c ON c.id = er.constituency_id
                WHERE c.chamber = :ch AND er.result = 'Won'
            """),
            {"ch": CHAMBER},
        ).scalar()
        total_pols = conn.execute(text("SELECT COUNT(*) FROM politicians")).scalar()

        # Year range
        year_range = conn.execute(
            text("""
                SELECT MIN(er.election_year), MAX(er.election_year)
                FROM election_records er
                JOIN constituencies c ON c.id = er.constituency_id
                WHERE c.chamber = :ch
            """),
            {"ch": CHAMBER},
        ).fetchone()

        # Top 5 states by election count
        top_states = conn.execute(
            text("""
                SELECT c.state, COUNT(*) as cnt
                FROM election_records er
                JOIN constituencies c ON c.id = er.constituency_id
                WHERE c.chamber = :ch
                GROUP BY c.state ORDER BY cnt DESC LIMIT 5
            """),
            {"ch": CHAMBER},
        ).fetchall()

    logger.info(f"\nValidation:")
    logger.info(f"  Vidhan Sabha constituencies: {vs_const}")
    logger.info(f"  Vidhan Sabha elections:       {vs_elec}")
    logger.info(f"  Vidhan Sabha winners:         {vs_winners}")
    logger.info(f"  Total politicians (all):      {total_pols}")
    if year_range:
        logger.info(f"  Year range: {year_range[0]} - {year_range[1]}")
    logger.info(f"  Top states by election count:")
    for state, cnt in top_states:
        logger.info(f"    {state}: {cnt}")


if __name__ == "__main__":
    main()
