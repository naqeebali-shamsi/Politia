"""
Bulk ingestion for individual parliamentary question records.
Reads semicolon-delimited CSVs from activity/Questions/Lok Sabha/,
matches MPs to existing politicians via entity resolution, and
bulk inserts ~400K question records.
"""
import csv
import sys
import time
import logging
import re
from pathlib import Path
from datetime import date
from collections import Counter

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.config import get_settings
from app.infrastructure.database.session import get_engine, Base
from app.infrastructure.ingestion.entity_resolver import (
    normalize_name,
    clean_name_for_storage,
)
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ingest_questions")

DATA_ROOT = _PROJECT_ROOT / "data"
QUESTIONS_DIR = (
    DATA_ROOT / "india-representatives-activity" / "activity" / "Questions" / "Lok Sabha"
)

# Map CSV filename to Lok Sabha term number
TERM_MAP = {
    "15th.csv": 15,
    "16th.csv": 16,
    "17th.csv": 17,
    "18th.csv": 18,
}


def parse_date(date_str: str):
    """Parse date string in YYYY-MM-DD format, return date or None."""
    date_str = date_str.strip().strip('"')
    if not date_str:
        return None
    try:
        parts = date_str.split("-")
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        return None


def build_politician_lookup(conn):
    """
    Build lookup dicts from the existing politicians table.
    Returns:
      by_name  - {normalized_name: politician_id}
      by_tokens - {frozenset(name_tokens): politician_id}
                  (only for names with 2+ tokens to avoid false matches)
    """
    rows = conn.execute(
        text("SELECT id, full_name, current_constituency FROM politicians")
    ).fetchall()

    by_name = {}  # norm_name -> id
    by_tokens = {}  # frozenset(tokens) -> id

    for pid, full_name, constituency in rows:
        norm = normalize_name(full_name)
        by_name[norm] = pid

        # Token-set lookup handles name-order reversal:
        # "SURESH KODIKUNNIL" matches "KODIKUNNIL SURESH"
        tokens = frozenset(norm.split())
        if len(tokens) >= 2:
            by_tokens[tokens] = pid

    logger.info(f"  Loaded {len(rows)} politicians, {len(by_name)} unique names, "
                f"{len(by_tokens)} token-sets")
    return by_name, by_tokens


def ingest_questions():
    engine = get_engine()

    # Import models so Base knows about question_records table
    import app.infrastructure.database.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Tables created/verified")

    t0 = time.monotonic()

    # Build politician lookup
    logger.info("Loading politician lookup...")
    with engine.connect() as conn:
        by_name, by_tokens = build_politician_lookup(conn)

    # Parse all question CSVs
    logger.info("Parsing question CSVs...")
    question_values = []
    total_rows = 0
    matched_count = 0
    unmatched_names = Counter()
    ministry_counts = Counter()

    for csv_file in sorted(QUESTIONS_DIR.glob("*.csv")):
        term_number = TERM_MAP.get(csv_file.name)
        if term_number is None:
            logger.warning(f"  Skipping unknown file: {csv_file.name}")
            continue

        logger.info(f"  Processing {csv_file.name} (term {term_number})...")
        file_count = 0
        file_matched = 0

        with open(csv_file, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                total_rows += 1
                file_count += 1

                rep_name = (row.get("Representative") or "").strip().strip('"')
                if not rep_name:
                    continue

                norm = normalize_name(rep_name)
                clean = clean_name_for_storage(rep_name)

                # Try exact normalized name match
                pid = by_name.get(norm)

                # Fallback: try cleaned name
                if not pid:
                    pid = by_name.get(normalize_name(clean))

                # Fallback: token-set match (handles name-order reversal)
                if not pid:
                    tokens = frozenset(norm.split())
                    if len(tokens) >= 2:
                        pid = by_tokens.get(tokens)

                if not pid:
                    unmatched_names[norm] += 1
                    continue

                matched_count += 1
                file_matched += 1

                ministry = (row.get("Ministry or Category") or "").strip().strip('"')
                q_type = (row.get("Type") or "").strip().strip('"')
                title = (row.get("Title") or "").strip().strip('"')
                link = (row.get("link") or "").strip().strip('"')
                q_date = parse_date(row.get("Date") or "")

                ministry_counts[ministry] += 1

                question_values.append({
                    "politician_id": pid,
                    "term_number": term_number,
                    "question_date": q_date.isoformat() if q_date else None,
                    "ministry": ministry if ministry else None,
                    "question_type": q_type if q_type else None,
                    "question_title": title if title else None,
                    "source_url": link if link else None,
                })

        logger.info(
            f"    {csv_file.name}: {file_count} rows, {file_matched} matched "
            f"({file_matched / file_count * 100:.1f}%)"
        )

    logger.info(f"Total parsed: {total_rows} rows, {matched_count} matched, "
                f"{total_rows - matched_count} unmatched")

    # Clear existing question records and bulk insert
    logger.info("Inserting question records...")
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM question_records"))
        logger.info("  Cleared existing question records")

        batch_size = 2000
        for i in range(0, len(question_values), batch_size):
            batch = question_values[i : i + batch_size]
            conn.execute(
                text(
                    "INSERT INTO question_records "
                    "(politician_id, term_number, question_date, ministry, "
                    "question_type, question_title, source_url) "
                    "VALUES (:politician_id, :term_number, :question_date, :ministry, "
                    ":question_type, :question_title, :source_url)"
                ),
                batch,
            )
            if (i // batch_size) % 25 == 0:
                logger.info(f"  Inserted {min(i + batch_size, len(question_values))}/{len(question_values)}")

        logger.info(f"  Inserted {len(question_values)} question records")

    elapsed = time.monotonic() - t0

    # Print stats
    print("\n" + "=" * 60)
    print("QUESTION INGESTION COMPLETE")
    print("=" * 60)
    print(f"  Time:              {elapsed:.1f}s")
    print(f"  Total CSV rows:    {total_rows}")
    print(f"  Matched:           {matched_count} ({matched_count / total_rows * 100:.1f}%)")
    print(f"  Unmatched:         {total_rows - matched_count}")
    print(f"  Records inserted:  {len(question_values)}")

    print(f"\nTop 10 ministries by question volume:")
    for ministry, count in ministry_counts.most_common(10):
        print(f"  {count:>7,}  {ministry}")

    if unmatched_names:
        print(f"\nTop 15 unmatched MP names:")
        for name, count in unmatched_names.most_common(15):
            print(f"  {count:>5}  {name}")


if __name__ == "__main__":
    ingest_questions()
