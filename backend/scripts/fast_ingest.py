"""
Fast bulk ingestion for remote databases (Neon PostgreSQL).
Uses raw SQL bulk inserts instead of row-by-row ORM operations.
Reduces network round-trips from ~75K to ~50.
"""
import csv
import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timezone

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.config import get_settings
from app.infrastructure.database.session import get_engine, Base
from app.infrastructure.ingestion.entity_resolver import normalize_name
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("fast_ingest")

DATA_ROOT = _PROJECT_ROOT / "data"


def bulk_ingest():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created/verified")

    t0 = time.monotonic()

    # ==================== PHASE 1: Elections ====================
    logger.info("PHASE 1: Loading election data...")
    csv_path = DATA_ROOT / "india-election-data" / "parliament-elections" / "parliament.csv"
    rows = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    logger.info(f"  Loaded {len(rows)} rows")

    # Build unique constituencies
    constituencies = {}  # (name, state) -> id
    const_id = 0
    for row in rows:
        pc = (row.get("PC") or "").strip().upper()
        state = (row.get("STATE") or "").strip().upper()
        if pc and state and (pc, state) not in constituencies:
            const_id += 1
            constituencies[(pc, state)] = const_id

    # Build unique politicians
    politicians = {}  # (normalized_name, constituency) -> id
    pol_id = 0
    pol_records = []  # (id, full_name, party, state, constituency, chamber, gender, is_active)

    for row in rows:
        name = (row.get("NAME") or "").strip().upper()
        pc = (row.get("PC") or "").strip().upper()
        state = (row.get("STATE") or "").strip().upper()
        party = (row.get("PARTY") or "").strip()
        sex = (row.get("SEX") or "").strip()
        pos = (row.get("#") or "99").strip()
        year = int((row.get("YEAR") or "0").strip() or "0")

        if not name or not pc:
            continue

        norm = normalize_name(name)
        key = (norm, pc)

        if key not in politicians:
            pol_id += 1
            politicians[key] = pol_id
            gender = "Male" if sex in ("M", "MALE") else ("Female" if sex in ("F", "FEMALE") else None)
            pol_records.append({
                "id": pol_id, "full_name": name, "current_party": party,
                "current_state": state, "current_constituency": pc,
                "current_chamber": "Lok Sabha", "gender": gender,
                "is_active": pos == "1",
            })
        else:
            # Update to latest election data
            existing_id = politicians[key]
            for rec in pol_records:
                if rec["id"] == existing_id:
                    if pos == "1":
                        rec["is_active"] = True
                    rec["current_party"] = party
                    break

    logger.info(f"  {len(constituencies)} constituencies, {len(politicians)} politicians")

    # Bulk insert constituencies
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM election_records"))
        conn.execute(text("DELETE FROM activity_records"))
        conn.execute(text("DELETE FROM disclosure_records"))
        conn.execute(text("DELETE FROM score_records"))
        conn.execute(text("DELETE FROM offices"))
        conn.execute(text("DELETE FROM politicians"))
        conn.execute(text("DELETE FROM constituencies"))
        conn.execute(text("DELETE FROM source_records"))
        logger.info("  Cleared existing data")

        # Insert constituencies
        const_values = [
            {"id": cid, "name": name, "state": state, "chamber": "Lok Sabha"}
            for (name, state), cid in constituencies.items()
        ]
        if const_values:
            for i in range(0, len(const_values), 1000):
                batch = const_values[i:i+1000]
                conn.execute(
                    text("INSERT INTO constituencies (id, name, state, chamber) VALUES (:id, :name, :state, :chamber)"),
                    batch
                )
            logger.info(f"  Inserted {len(const_values)} constituencies")

        # Insert politicians
        if pol_records:
            for i in range(0, len(pol_records), 1000):
                batch = pol_records[i:i+1000]
                conn.execute(
                    text("""INSERT INTO politicians (id, full_name, current_party, current_state,
                            current_constituency, current_chamber, gender, is_active)
                            VALUES (:id, :full_name, :current_party, :current_state,
                            :current_constituency, :current_chamber, :gender, :is_active)"""),
                    batch
                )
            logger.info(f"  Inserted {len(pol_records)} politicians")

        # Insert election records
        election_values = []
        for row in rows:
            name = (row.get("NAME") or "").strip().upper()
            pc = (row.get("PC") or "").strip().upper()
            state = (row.get("STATE") or "").strip().upper()
            party = (row.get("PARTY") or "").strip()
            year_str = (row.get("YEAR") or "0").strip()
            votes_str = (row.get("VOTES") or "0").strip()
            pos_str = (row.get("#") or "99").strip()

            if not name or not pc:
                continue

            norm = normalize_name(name)
            pid = politicians.get((norm, pc))
            cid = constituencies.get((pc, state))
            year = int(year_str) if year_str.isdigit() else 0
            votes = int(votes_str) if votes_str.isdigit() else 0
            pos = int(pos_str) if pos_str.isdigit() else 99

            if pid and year:
                election_values.append({
                    "politician_id": pid, "constituency_id": cid,
                    "election_year": year, "election_type": "General",
                    "party": party, "result": "Won" if pos == 1 else "Lost",
                    "votes": votes if votes > 0 else None,
                })

        for i in range(0, len(election_values), 1000):
            batch = election_values[i:i+1000]
            conn.execute(
                text("""INSERT INTO election_records (politician_id, constituency_id, election_year,
                        election_type, party, result, votes)
                        VALUES (:politician_id, :constituency_id, :election_year,
                        :election_type, :party, :result, :votes)"""),
                batch
            )
        logger.info(f"  Inserted {len(election_values)} election records")

    logger.info(f"PHASE 1 done: {time.monotonic()-t0:.1f}s")

    # ==================== PHASE 2: Affidavits ====================
    t1 = time.monotonic()
    logger.info("PHASE 2: Loading affidavit data...")
    aff_path = DATA_ROOT / "parliamentary-candidates-affidavit-data" / "2004-2019-affidavits.csv"
    aff_rows = []
    with open(aff_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            aff_rows.append(row)
    logger.info(f"  Loaded {len(aff_rows)} rows")

    disc_values = []
    matched = 0
    for row in aff_rows:
        name = (row.get("Candidate") or "").strip().upper()
        pc = (row.get("Constituency") or "").strip().upper()
        year = int(row.get("Year") or 0)
        if not name or not pc or not year:
            continue

        norm = normalize_name(name)
        pid = politicians.get((norm, pc))
        if not pid:
            continue
        matched += 1

        def safe_float(v):
            if not v or v in ("NA", "N/A", "None", "-"):
                return None
            try:
                return float(str(v).replace(",", ""))
            except ValueError:
                return None

        disc_values.append({
            "politician_id": pid, "election_year": year,
            "total_assets": safe_float(row.get("TotalAssets")),
            "total_liabilities": safe_float(row.get("TotalLiabilities")),
            "criminal_cases": int(row.get("CriminalCases") or 0),
            "affidavit_complete": row.get("TotalAssets") not in (None, "", "NA"),
        })

    with engine.begin() as conn:
        for i in range(0, len(disc_values), 1000):
            batch = disc_values[i:i+1000]
            conn.execute(
                text("""INSERT INTO disclosure_records (politician_id, election_year, total_assets,
                        total_liabilities, criminal_cases, affidavit_complete)
                        VALUES (:politician_id, :election_year, :total_assets,
                        :total_liabilities, :criminal_cases, :affidavit_complete)"""),
                batch
            )
        logger.info(f"  Matched {matched}/{len(aff_rows)}, inserted {len(disc_values)} disclosures")

        # Update education on politicians
        for row in aff_rows:
            name = (row.get("Candidate") or "").strip().upper()
            pc = (row.get("Constituency") or "").strip().upper()
            edu = (row.get("Education") or "").strip()
            norm = normalize_name(name)
            pid = politicians.get((norm, pc))
            if pid and edu and edu not in ("NA", "N/A"):
                conn.execute(
                    text("UPDATE politicians SET education = :edu WHERE id = :pid AND education IS NULL"),
                    {"edu": edu, "pid": pid}
                )

    logger.info(f"PHASE 2 done: {time.monotonic()-t1:.1f}s")

    # ==================== PHASE 3: Activity ====================
    t2 = time.monotonic()
    logger.info("PHASE 3: Loading PRS activity data...")
    activity_dir = DATA_ROOT / "india-representatives-activity" / "csv" / "Lok Sabha"
    act_values = []

    for csv_file in sorted(activity_dir.glob("*.csv")):
        logger.info(f"  Processing {csv_file.name}")
        with open(csv_file, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f, delimiter=";"):
                name = (row.get("Name") or "").strip().strip('"')
                pc = (row.get("Constituency") or "").strip().strip('"').upper()
                ls = (row.get("Lok Sabha") or "").strip().strip('"')

                if not name:
                    continue

                norm = normalize_name(name)
                pid = politicians.get((norm, pc))
                if not pid:
                    # Try without constituency match
                    for (pn, _), p_id in politicians.items():
                        if pn == norm:
                            pid = p_id
                            break
                if not pid:
                    continue

                term = None
                for ch in ls:
                    if ch.isdigit():
                        term = int("".join(c for c in ls if c.isdigit()))
                        break

                att_str = (row.get("Attendance") or "0").strip().strip('"').replace("%", "")
                try:
                    attendance = float(att_str) if att_str else 0
                except ValueError:
                    attendance = 0

                debates = int(float((row.get("Debates") or "0").strip().strip('"') or "0"))
                questions = int(float((row.get("Questions") or "0").strip().strip('"') or "0"))
                bills = int(float((row.get("Private Member Bills") or "0").strip().strip('"') or "0"))

                act_values.append({
                    "politician_id": pid, "term_number": term,
                    "session_name": f"{ls} Lok Sabha" if ls else None,
                    "attendance_percentage": attendance,
                    "questions_asked": questions,
                    "debates_participated": debates,
                    "private_bills_introduced": bills,
                })

    with engine.begin() as conn:
        for i in range(0, len(act_values), 1000):
            batch = act_values[i:i+1000]
            conn.execute(
                text("""INSERT INTO activity_records (politician_id, term_number, session_name,
                        attendance_percentage, questions_asked, debates_participated, private_bills_introduced)
                        VALUES (:politician_id, :term_number, :session_name,
                        :attendance_percentage, :questions_asked, :debates_participated, :private_bills_introduced)"""),
                batch
            )
        logger.info(f"  Inserted {len(act_values)} activity records")

    logger.info(f"PHASE 3 done: {time.monotonic()-t2:.1f}s")

    # ==================== PHASE 4: Scoring ====================
    t3 = time.monotonic()
    logger.info("PHASE 4: Computing scores...")

    from app.infrastructure.scoring.engine import ScoringEngine
    scoring = ScoringEngine()

    with engine.begin() as conn:
        # Get baselines
        row = conn.execute(text("""
            SELECT AVG(attendance_percentage), AVG(questions_asked), AVG(debates_participated)
            FROM activity_records
        """)).fetchone()
        baselines = {
            "avg_attendance": float(row[0] or 0),
            "avg_questions": float(row[1] or 0),
            "avg_debates": float(row[2] or 0),
        }
        logger.info(f"  Baselines: {baselines}")

        # Score each politician
        score_values = []
        for (_, _), pid in politicians.items():
            # Get latest activity
            act = conn.execute(text(
                "SELECT attendance_percentage, questions_asked, debates_participated, committee_memberships "
                "FROM activity_records WHERE politician_id = :pid ORDER BY term_number DESC LIMIT 1"
            ), {"pid": pid}).fetchone()

            participation_data = {}
            if act:
                participation_data = {
                    "attendance_percentage": act[0], "questions_asked": act[1],
                    "debates_participated": act[2], "committee_memberships": act[3] or 0,
                }

            # Get latest disclosure
            disc = conn.execute(text(
                "SELECT total_assets, total_liabilities, criminal_cases, serious_criminal_cases, "
                "affidavit_complete, pan_declared FROM disclosure_records "
                "WHERE politician_id = :pid ORDER BY election_year DESC LIMIT 1"
            ), {"pid": pid}).fetchone()

            disclosure_data = {}
            integrity_data = {}
            if disc:
                disclosure_data = {
                    "affidavit_complete": disc[4], "total_assets": disc[0],
                    "total_liabilities": disc[1], "pan_declared": disc[5] or False,
                }
                integrity_data = {"criminal_cases": disc[2] or 0, "serious_criminal_cases": disc[3] or 0}

            # Count elections for disclosure linkage
            elec_count = conn.execute(text(
                "SELECT COUNT(*) FROM election_records WHERE politician_id = :pid"
            ), {"pid": pid}).scalar()
            disclosure_data["election_count"] = elec_count

            score = scoring.compute_score(pid, participation_data, disclosure_data, integrity_data, baselines)
            score_values.append({
                "politician_id": pid, "overall_score": score.overall_score,
                "participation_score": score.participation_score,
                "disclosure_score": score.disclosure_score,
                "integrity_risk_adjustment": score.integrity_risk_adjustment,
                "formula_version": score.formula_version, "is_current": True,
            })

        for i in range(0, len(score_values), 1000):
            batch = score_values[i:i+1000]
            conn.execute(
                text("""INSERT INTO score_records (politician_id, overall_score, participation_score,
                        disclosure_score, integrity_risk_adjustment, formula_version, is_current)
                        VALUES (:politician_id, :overall_score, :participation_score,
                        :disclosure_score, :integrity_risk_adjustment, :formula_version, :is_current)"""),
                batch
            )
        logger.info(f"  Computed and inserted {len(score_values)} scores")

    logger.info(f"PHASE 4 done: {time.monotonic()-t3:.1f}s")

    total = time.monotonic() - t0
    logger.info(f"{'='*50}")
    logger.info(f"COMPLETE in {total:.1f}s")
    logger.info(f"  {len(constituencies)} constituencies")
    logger.info(f"  {len(politicians)} politicians")
    logger.info(f"  {len(election_values)} elections")
    logger.info(f"  {len(disc_values)} disclosures")
    logger.info(f"  {len(act_values)} activities")
    logger.info(f"  {len(score_values)} scores")


if __name__ == "__main__":
    bulk_ingest()
