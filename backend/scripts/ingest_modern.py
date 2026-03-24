"""
P0-1: Ingest 2014 + 2024 election data into Politia.
Uses the fixed entity resolver (P0-3) with state normalization,
temporal plausibility, and over-merge prevention.

Usage: python scripts/ingest_modern.py
"""
import csv
import sys
import time
import logging
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.infrastructure.database.session import get_engine, Base
from app.infrastructure.ingestion.entity_resolver import (
    normalize_name, clean_name_for_storage, normalize_state, match_names,
    is_common_name, should_merge,
)
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("ingest_modern")

DATA_ROOT = _PROJECT_ROOT / "data"


def read_2014_eci(path: Path) -> list[dict]:
    """Read datameet 2014 ECI candidate-wise CSV."""
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            name = (row.get("Candidate") or "").strip().upper()
            party = (row.get("Party") or "").strip()
            votes = int(row.get("Votes") or 0)
            state = (row.get("State") or "").strip().upper()
            constituency = (row.get("Constituency") or "").strip().upper()
            if name and constituency:
                rows.append({
                    "year": 2014, "name": clean_name_for_storage(name),
                    "party": party, "votes": votes,
                    "state": normalize_state(state),
                    "constituency": constituency,
                })
    return rows


def read_2024_opencity(path: Path) -> list[dict]:
    """Read OpenCity 2024 election results CSV."""
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            name = (row.get("Candidate") or "").strip().upper()
            party = (row.get("Party") or "").strip()
            total_votes = row.get("Total Votes") or row.get("Votes") or "0"
            votes_str = str(total_votes).replace(",", "").strip()
            votes = int(votes_str) if votes_str.isdigit() else 0
            state = (row.get("State") or "").strip().upper()
            constituency = (row.get("PC Name") or row.get("Constituency") or "").strip().upper()
            if name and constituency:
                rows.append({
                    "year": 2024, "name": clean_name_for_storage(name),
                    "party": party, "votes": votes,
                    "state": normalize_state(state),
                    "constituency": constituency,
                })
    return rows


def read_2019_eci(path: Path) -> list[dict]:
    """Read pratapvardhan 2019 ECI-scraped CSV."""
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            name = (row.get("Candidate") or "").strip().upper()
            party = (row.get("Party") or "").strip()
            total_votes = row.get("Total Votes") or "0"
            votes_str = str(total_votes).replace(",", "").strip()
            votes = int(votes_str) if votes_str.isdigit() else 0
            state = (row.get("State") or "").strip().upper()
            constituency = (row.get("Constituency") or "").strip().upper()
            if name and constituency:
                rows.append({
                    "year": 2019, "name": clean_name_for_storage(name),
                    "party": party, "votes": votes,
                    "state": normalize_state(state),
                    "constituency": constituency,
                })
    return rows


def determine_winners(rows: list[dict]) -> list[dict]:
    """Mark position=1 for the candidate with most votes per constituency per year."""
    from collections import defaultdict
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
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    t0 = time.monotonic()

    # Load existing data to build lookup caches
    logger.info("Loading existing data from DB...")
    with engine.connect() as conn:
        existing_constituencies = {}
        for r in conn.execute(text("SELECT id, name, state FROM constituencies")).fetchall():
            existing_constituencies[(r[1], r[2])] = r[0]

        existing_politicians = {}  # (normalized_name, constituency, state) -> id
        for r in conn.execute(text("SELECT id, full_name, current_constituency, current_state FROM politicians")).fetchall():
            norm = normalize_name(r[1])
            state = normalize_state(r[3] or "")
            existing_politicians[(norm, r[2] or "", state)] = r[0]

        existing_elections = set()
        for r in conn.execute(text("SELECT politician_id, election_year, constituency_id FROM election_records")).fetchall():
            existing_elections.add((r[0], r[1], r[2]))

        max_pol_id = conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM politicians")).scalar()
        max_const_id = conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM constituencies")).scalar()

    logger.info(f"  {len(existing_constituencies)} constituencies, {len(existing_politicians)} politicians, {len(existing_elections)} elections")

    # Read new data
    all_rows = []

    # 2014 data
    path_2014 = DATA_ROOT / "india-election-data" / "parliament-elections" / "election2014" / "eci-candidate-wise.csv"
    if path_2014.exists():
        rows_2014 = read_2014_eci(path_2014)
        logger.info(f"Loaded {len(rows_2014)} rows from 2014 ECI data")
        all_rows.extend(rows_2014)

    # 2019 data
    path_2019 = DATA_ROOT / "lok-sabha-2019" / "eci-2019.csv"
    if path_2019.exists():
        rows_2019 = read_2019_eci(path_2019)
        logger.info(f"Loaded {len(rows_2019)} rows from 2019 ECI data")
        all_rows.extend(rows_2019)

    # 2024 data
    path_2024 = DATA_ROOT / "election-2024" / "results-2024.csv"
    if path_2024.exists():
        rows_2024 = read_2024_opencity(path_2024)
        logger.info(f"Loaded {len(rows_2024)} rows from 2024 OpenCity data")
        all_rows.extend(rows_2024)

    if not all_rows:
        logger.error("No data files found!")
        return

    # Determine winners by highest vote count per seat
    all_rows = determine_winners(all_rows)

    # Process: create new constituencies, politicians, elections
    new_constituencies = []
    new_politicians = []
    new_elections = []
    next_const_id = max_const_id + 1
    next_pol_id = max_pol_id + 1
    stats = {"const_created": 0, "pol_created": 0, "pol_matched": 0, "elec_created": 0, "elec_skipped": 0}

    for row in all_rows:
        name = row["name"]
        constituency = row["constituency"]
        state = row["state"]
        year = row["year"]
        party = row["party"]
        votes = row["votes"]
        position = row.get("position", 99)

        # Constituency: get or create
        const_key = (constituency, state)
        if const_key not in existing_constituencies:
            existing_constituencies[const_key] = next_const_id
            new_constituencies.append({
                "id": next_const_id, "name": constituency,
                "state": state, "chamber": "Lok Sabha",
            })
            next_const_id += 1
            stats["const_created"] += 1
        const_id = existing_constituencies[const_key]

        # Politician: match or create
        norm = normalize_name(name)
        pol_key = (norm, constituency, state)
        pol_id = existing_politicians.get(pol_key)

        if pol_id is None:
            # Try fuzzy match against existing politicians in same state
            best_match_id = None
            best_score = 0
            for (pn, pc, ps), pid in existing_politicians.items():
                if ps != state:
                    continue
                # For common names, require same constituency
                if is_common_name(name) and pc != constituency:
                    continue
                score = match_names(name, pn)
                if score > best_score and score >= 85.0:
                    # Extra check: if different constituency, need very high score
                    if pc != constituency and score < 92.0:
                        continue
                    best_score = score
                    best_match_id = pid

            if best_match_id:
                pol_id = best_match_id
                existing_politicians[pol_key] = pol_id
                stats["pol_matched"] += 1
            else:
                pol_id = next_pol_id
                existing_politicians[pol_key] = pol_id
                new_politicians.append({
                    "id": pol_id, "full_name": name,
                    "current_party": party, "current_state": state,
                    "current_constituency": constituency,
                    "current_chamber": "Lok Sabha",
                    "is_active": position == 1,
                })
                next_pol_id += 1
                stats["pol_created"] += 1

        # Election record: dedup
        dedup_key = (pol_id, year, const_id)
        if dedup_key in existing_elections:
            stats["elec_skipped"] += 1
            continue
        existing_elections.add(dedup_key)

        new_elections.append({
            "politician_id": pol_id, "constituency_id": const_id,
            "election_year": year, "election_type": "General",
            "party": party, "result": "Won" if position == 1 else "Lost",
            "votes": votes if votes > 0 else None,
        })
        stats["elec_created"] += 1

    # Bulk insert
    logger.info(f"Inserting: {stats['const_created']} constituencies, {stats['pol_created']} politicians, {stats['elec_created']} elections")
    logger.info(f"Matched {stats['pol_matched']} politicians to existing records, skipped {stats['elec_skipped']} duplicate elections")

    with engine.begin() as conn:
        if new_constituencies:
            for i in range(0, len(new_constituencies), 1000):
                conn.execute(
                    text("INSERT INTO constituencies (id, name, state, chamber) VALUES (:id, :name, :state, :chamber)"),
                    new_constituencies[i:i+1000]
                )

        if new_politicians:
            for i in range(0, len(new_politicians), 1000):
                conn.execute(
                    text("""INSERT INTO politicians (id, full_name, current_party, current_state,
                            current_constituency, current_chamber, is_active)
                            VALUES (:id, :full_name, :current_party, :current_state,
                            :current_constituency, :current_chamber, :is_active)"""),
                    new_politicians[i:i+1000]
                )

        if new_elections:
            for i in range(0, len(new_elections), 1000):
                conn.execute(
                    text("""INSERT INTO election_records (politician_id, constituency_id, election_year,
                            election_type, party, result, votes)
                            VALUES (:politician_id, :constituency_id, :election_year,
                            :election_type, :party, :result, :votes)"""),
                    new_elections[i:i+1000]
                )

        # Update is_active for winners of latest election
        conn.execute(text("UPDATE politicians SET is_active = false"))
        conn.execute(text("""
            UPDATE politicians SET is_active = true, current_party = sub.party,
                   current_constituency = sub.constituency, current_state = sub.state
            FROM (
                SELECT er.politician_id, er.party, c.name as constituency, c.state
                FROM election_records er
                JOIN constituencies c ON c.id = er.constituency_id
                WHERE er.election_year = (SELECT MAX(election_year) FROM election_records)
                  AND er.result = 'Won'
            ) sub
            WHERE politicians.id = sub.politician_id
        """))

    elapsed = time.monotonic() - t0
    logger.info(f"DONE in {elapsed:.1f}s")

    # Validation
    with engine.connect() as conn:
        for year in [2014, 2024]:
            count = conn.execute(text(f"SELECT COUNT(*) FROM election_records WHERE election_year = {year}")).scalar()
            winners = conn.execute(text(f"SELECT COUNT(*) FROM election_records WHERE election_year = {year} AND result = 'Won'")).scalar()
            logger.info(f"  {year}: {count} records, {winners} winners")

        total_pols = conn.execute(text("SELECT COUNT(*) FROM politicians")).scalar()
        active = conn.execute(text("SELECT COUNT(*) FROM politicians WHERE is_active = true")).scalar()
        total_elec = conn.execute(text("SELECT COUNT(*) FROM election_records")).scalar()
        logger.info(f"  Total: {total_pols} politicians, {active} active, {total_elec} elections")


if __name__ == "__main__":
    main()
