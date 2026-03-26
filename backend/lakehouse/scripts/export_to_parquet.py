"""
Bronze Layer: Export all SQLite tables to Parquet files as-is.

Uses DuckDB's SQLite scanner to read tables directly, then writes
Parquet with zstd compression into lakehouse/bronze/.
"""
import sys
import time
from pathlib import Path

import duckdb

# Paths
BACKEND_DIR = Path(__file__).resolve().parents[2]
SQLITE_PATH = BACKEND_DIR / "politia_dev.db"
BRONZE_DIR = BACKEND_DIR / "lakehouse" / "bronze"

TABLES = [
    "politicians",
    "election_records",
    "disclosure_records",
    "activity_records",
    "constituencies",
    "score_records",
    "source_records",
]


def export_table(con: duckdb.DuckDBPyConnection, table_name: str) -> tuple[int, int]:
    """Export a single table to Parquet. Returns (row_count, file_size_bytes)."""
    out_path = BRONZE_DIR / f"{table_name}.parquet"

    con.execute(f"""
        COPY (SELECT * FROM sqlite_scan('{SQLITE_PATH}', '{table_name}'))
        TO '{out_path}'
        (FORMAT PARQUET, COMPRESSION ZSTD);
    """)

    rows = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out_path}')").fetchone()[0]
    return rows, out_path.stat().st_size


def main() -> None:
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(database=":memory:")
    con.install_extension("sqlite")
    con.load_extension("sqlite")

    print("=" * 60)
    print("BRONZE LAYER: SQLite -> Parquet export")
    print("=" * 60)
    print(f"Source : {SQLITE_PATH}")
    print(f"Target : {BRONZE_DIR}")
    print()

    total_rows = 0
    total_bytes = 0
    t0 = time.perf_counter()

    for table in TABLES:
        try:
            rows, size = export_table(con, table)
            total_rows += rows
            total_bytes += size
            print(f"  {table:25s}  {rows:>8,} rows  {size / 1024:>8.1f} KB")
        except Exception as exc:
            print(f"  {table:25s}  ERROR: {exc}", file=sys.stderr)

    elapsed = time.perf_counter() - t0
    print()
    print(f"Total rows  : {total_rows:,}")
    print(f"Total size  : {total_bytes / 1024:.1f} KB ({total_bytes / 1024 / 1024:.2f} MB)")
    print(f"Elapsed     : {elapsed:.2f}s")

    con.close()


if __name__ == "__main__":
    main()
