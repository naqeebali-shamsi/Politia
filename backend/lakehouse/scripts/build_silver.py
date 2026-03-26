"""
Silver Layer: Clean, normalize, and deduplicate bronze Parquet files.

Operations:
  - Normalize state names (uppercase, trim, canonical mapping)
  - Clean politician names (title-case, strip extra whitespace)
  - Deduplicate election records on (politician_id, election_year, constituency_id)
  - Partition output by state and year where applicable
"""
import sys
import time
from pathlib import Path

import polars as pl

BACKEND_DIR = Path(__file__).resolve().parents[2]
BRONZE_DIR = BACKEND_DIR / "lakehouse" / "bronze"
SILVER_DIR = BACKEND_DIR / "lakehouse" / "silver"

# Canonical state name mapping (common variations -> standard)
STATE_NORMALISATION: dict[str, str] = {
    "A & N ISLANDS": "ANDAMAN AND NICOBAR ISLANDS",
    "A&N ISLANDS": "ANDAMAN AND NICOBAR ISLANDS",
    "ANDAMAN & NICOBAR ISLANDS": "ANDAMAN AND NICOBAR ISLANDS",
    "D & N HAVELI": "DADRA AND NAGAR HAVELI",
    "D&N HAVELI": "DADRA AND NAGAR HAVELI",
    "DADRA & NAGAR HAVELI": "DADRA AND NAGAR HAVELI",
    "DAMAN & DIU": "DAMAN AND DIU",
    "J & K": "JAMMU AND KASHMIR",
    "JAMMU & KASHMIR": "JAMMU AND KASHMIR",
    "DELHI": "NCT OF DELHI",
    "PONDICHERRY": "PUDUCHERRY",
    "ORISSA": "ODISHA",
    "UTTARANCHAL": "UTTARAKHAND",
    "CHATTISGARH": "CHHATTISGARH",
    "CHHATISGARH": "CHHATTISGARH",
}


def normalize_state(s: str | None) -> str | None:
    if s is None:
        return None
    s = s.strip().upper()
    return STATE_NORMALISATION.get(s, s)


def clean_name(name: str | None) -> str | None:
    if name is None:
        return None
    # Collapse whitespace, strip, title-case
    import re
    name = re.sub(r"\s+", " ", name.strip())
    return name.title()


def build_silver_politicians() -> tuple[int, int]:
    """Clean politicians table."""
    df = pl.read_parquet(BRONZE_DIR / "politicians.parquet")

    df = df.with_columns([
        pl.col("full_name").map_elements(clean_name, return_dtype=pl.Utf8).alias("full_name"),
        pl.col("current_state").map_elements(normalize_state, return_dtype=pl.Utf8).alias("current_state"),
        pl.col("current_party").str.strip_chars().str.to_uppercase().alias("current_party"),
    ])

    # Deduplicate on full_name + current_state (keep first by id)
    df = df.sort("id").unique(subset=["full_name", "current_state"], keep="first")

    out = SILVER_DIR / "politicians.parquet"
    df.write_parquet(out, compression="zstd")
    return len(df), out.stat().st_size


def build_silver_elections() -> tuple[int, int]:
    """Clean and partition election records."""
    df = pl.read_parquet(BRONZE_DIR / "election_records.parquet")

    # Normalize party names
    df = df.with_columns([
        pl.col("party").str.strip_chars().str.to_uppercase().alias("party"),
        pl.col("result").str.strip_chars().str.to_uppercase().alias("result"),
    ])

    # Deduplicate on (politician_id, election_year, constituency_id)
    df = df.sort("id").unique(
        subset=["politician_id", "election_year", "constituency_id"],
        keep="first",
    )

    # Join with politicians to get state for partitioning
    pols = pl.read_parquet(BRONZE_DIR / "politicians.parquet").select([
        pl.col("id").alias("politician_id"),
        pl.col("current_state").map_elements(normalize_state, return_dtype=pl.Utf8).alias("state"),
    ])
    df = df.join(pols, on="politician_id", how="left")

    # Write partitioned by election_year
    out_dir = SILVER_DIR / "election_records"
    out_dir.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    total_bytes = 0
    for year in sorted(df["election_year"].unique().to_list()):
        year_df = df.filter(pl.col("election_year") == year)
        out = out_dir / f"year={year}.parquet"
        year_df.write_parquet(out, compression="zstd")
        total_rows += len(year_df)
        total_bytes += out.stat().st_size

    return total_rows, total_bytes


def build_silver_disclosures() -> tuple[int, int]:
    """Clean disclosure records."""
    df = pl.read_parquet(BRONZE_DIR / "disclosure_records.parquet")

    # Deduplicate on (politician_id, election_year)
    df = df.sort("id").unique(
        subset=["politician_id", "election_year"],
        keep="first",
    )

    # Join state from politicians
    pols = pl.read_parquet(BRONZE_DIR / "politicians.parquet").select([
        pl.col("id").alias("politician_id"),
        pl.col("current_state").map_elements(normalize_state, return_dtype=pl.Utf8).alias("state"),
        pl.col("current_party").str.strip_chars().str.to_uppercase().alias("party"),
    ])
    df = df.join(pols, on="politician_id", how="left")

    out = SILVER_DIR / "disclosure_records.parquet"
    df.write_parquet(out, compression="zstd")
    return len(df), out.stat().st_size


def build_silver_constituencies() -> tuple[int, int]:
    """Clean constituencies."""
    df = pl.read_parquet(BRONZE_DIR / "constituencies.parquet")

    df = df.with_columns([
        pl.col("state").map_elements(normalize_state, return_dtype=pl.Utf8).alias("state"),
        pl.col("name").str.strip_chars().str.to_uppercase().alias("name"),
    ])

    df = df.sort("id").unique(subset=["name", "state", "chamber"], keep="first")

    out = SILVER_DIR / "constituencies.parquet"
    df.write_parquet(out, compression="zstd")
    return len(df), out.stat().st_size


def build_silver_scores() -> tuple[int, int]:
    """Pass through score records (already computed)."""
    df = pl.read_parquet(BRONZE_DIR / "score_records.parquet")

    out = SILVER_DIR / "score_records.parquet"
    df.write_parquet(out, compression="zstd")
    return len(df), out.stat().st_size


def build_silver_activities() -> tuple[int, int]:
    """Pass through activity records."""
    df = pl.read_parquet(BRONZE_DIR / "activity_records.parquet")

    out = SILVER_DIR / "activity_records.parquet"
    df.write_parquet(out, compression="zstd")
    return len(df), out.stat().st_size


def main() -> None:
    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("SILVER LAYER: Clean, normalize, deduplicate")
    print("=" * 60)
    print(f"Source : {BRONZE_DIR}")
    print(f"Target : {SILVER_DIR}")
    print()

    builders = [
        ("politicians", build_silver_politicians),
        ("elections", build_silver_elections),
        ("disclosures", build_silver_disclosures),
        ("constituencies", build_silver_constituencies),
        ("scores", build_silver_scores),
        ("activities", build_silver_activities),
    ]

    total_rows = 0
    total_bytes = 0
    t0 = time.perf_counter()

    for name, fn in builders:
        try:
            rows, size = fn()
            total_rows += rows
            total_bytes += size
            print(f"  {name:25s}  {rows:>8,} rows  {size / 1024:>8.1f} KB")
        except Exception as exc:
            print(f"  {name:25s}  ERROR: {exc}", file=sys.stderr)

    elapsed = time.perf_counter() - t0
    print()
    print(f"Total rows  : {total_rows:,}")
    print(f"Total size  : {total_bytes / 1024:.1f} KB ({total_bytes / 1024 / 1024:.2f} MB)")
    print(f"Elapsed     : {elapsed:.2f}s")


if __name__ == "__main__":
    main()
