"""
Gold Layer: Pre-aggregated analytical datasets for instant DuckDB queries.

Outputs:
  - party_performance.parquet  : party-wise seats won, vote share by year
  - state_trends.parquet       : state-wise electoral trends over time
  - wealth_trends.parquet      : crorepati counts, avg assets by year
  - criminal_trends.parquet    : criminal case counts by year, party, state
"""
import time
from pathlib import Path

import duckdb

BACKEND_DIR = Path(__file__).resolve().parents[2]
SILVER_DIR = BACKEND_DIR / "lakehouse" / "silver"
GOLD_DIR = BACKEND_DIR / "lakehouse" / "gold"


def _silver(name: str) -> str:
    """Return the path string for a silver-layer file or directory."""
    p = SILVER_DIR / name
    if p.is_dir():
        return str(p / "*.parquet")
    return str(p)


def build_party_performance(con: duckdb.DuckDBPyConnection) -> tuple[int, int]:
    """Party-wise seats won, total votes, avg vote share by year."""
    query = f"""
    COPY (
        SELECT
            election_year,
            party,
            COUNT(*)                                        AS candidates,
            SUM(CASE WHEN result = 'WON' THEN 1 ELSE 0 END) AS seats_won,
            SUM(votes)                                      AS total_votes,
            ROUND(AVG(vote_share), 2)                       AS avg_vote_share,
            ROUND(
                SUM(CASE WHEN result = 'WON' THEN 1 ELSE 0 END) * 100.0
                / NULLIF(COUNT(*), 0), 2
            )                                               AS win_rate
        FROM read_parquet('{_silver("election_records")}')
        GROUP BY election_year, party
        ORDER BY election_year, seats_won DESC
    ) TO '{GOLD_DIR / "party_performance.parquet"}'
    (FORMAT PARQUET, COMPRESSION ZSTD);
    """
    con.execute(query)
    out = GOLD_DIR / "party_performance.parquet"
    rows = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    return rows, out.stat().st_size


def build_state_trends(con: duckdb.DuckDBPyConnection) -> tuple[int, int]:
    """State-wise electoral trends: turnout proxy, competitiveness, dominant party."""
    query = f"""
    COPY (
        WITH state_year AS (
            SELECT
                state,
                election_year,
                COUNT(*)                                          AS total_candidates,
                SUM(CASE WHEN result = 'WON' THEN 1 ELSE 0 END) AS total_seats,
                SUM(votes)                                        AS total_votes,
                ROUND(AVG(vote_share), 2)                         AS avg_vote_share,
                -- Competitiveness: avg margin for winners
                ROUND(AVG(CASE WHEN result = 'WON' THEN margin END), 0) AS avg_winning_margin,
                -- Candidates per seat
                ROUND(COUNT(*) * 1.0 / NULLIF(SUM(CASE WHEN result = 'WON' THEN 1 ELSE 0 END), 0), 1) AS candidates_per_seat
            FROM read_parquet('{_silver("election_records")}')
            WHERE state IS NOT NULL
            GROUP BY state, election_year
        ),
        dominant AS (
            SELECT
                state,
                election_year,
                party,
                SUM(CASE WHEN result = 'WON' THEN 1 ELSE 0 END) AS party_seats,
                ROW_NUMBER() OVER (
                    PARTITION BY state, election_year
                    ORDER BY SUM(CASE WHEN result = 'WON' THEN 1 ELSE 0 END) DESC
                ) AS rn
            FROM read_parquet('{_silver("election_records")}')
            WHERE state IS NOT NULL
            GROUP BY state, election_year, party
        )
        SELECT
            sy.*,
            d.party AS dominant_party,
            d.party_seats AS dominant_party_seats
        FROM state_year sy
        LEFT JOIN dominant d
            ON sy.state = d.state
            AND sy.election_year = d.election_year
            AND d.rn = 1
        ORDER BY sy.state, sy.election_year
    ) TO '{GOLD_DIR / "state_trends.parquet"}'
    (FORMAT PARQUET, COMPRESSION ZSTD);
    """
    con.execute(query)
    out = GOLD_DIR / "state_trends.parquet"
    rows = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    return rows, out.stat().st_size


def build_wealth_trends(con: duckdb.DuckDBPyConnection) -> tuple[int, int]:
    """Crorepati counts, average assets, liability ratios by year."""
    query = f"""
    COPY (
        SELECT
            election_year,
            COUNT(*)                                            AS total_candidates,
            SUM(CASE WHEN total_assets >= 10000000 THEN 1 ELSE 0 END) AS crorepati_count,
            ROUND(
                SUM(CASE WHEN total_assets >= 10000000 THEN 1 ELSE 0 END) * 100.0
                / NULLIF(COUNT(*), 0), 1
            )                                                   AS crorepati_pct,
            ROUND(AVG(total_assets), 0)                         AS avg_assets,
            ROUND(MEDIAN(total_assets), 0)                      AS median_assets,
            ROUND(AVG(total_liabilities), 0)                    AS avg_liabilities,
            ROUND(AVG(movable_assets), 0)                       AS avg_movable,
            ROUND(AVG(immovable_assets), 0)                     AS avg_immovable
        FROM read_parquet('{_silver("disclosure_records.parquet")}')
        GROUP BY election_year
        ORDER BY election_year
    ) TO '{GOLD_DIR / "wealth_trends.parquet"}'
    (FORMAT PARQUET, COMPRESSION ZSTD);
    """
    con.execute(query)
    out = GOLD_DIR / "wealth_trends.parquet"
    rows = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    return rows, out.stat().st_size


def build_criminal_trends(con: duckdb.DuckDBPyConnection) -> tuple[int, int]:
    """Criminal case counts by year, party, state."""
    query = f"""
    COPY (
        SELECT
            election_year,
            COALESCE(party, 'UNKNOWN')   AS party,
            COALESCE(state, 'UNKNOWN')   AS state,
            COUNT(*)                      AS total_candidates,
            SUM(CASE WHEN criminal_cases > 0 THEN 1 ELSE 0 END) AS candidates_with_cases,
            SUM(criminal_cases)           AS total_criminal_cases,
            SUM(COALESCE(serious_criminal_cases, 0)) AS total_serious_cases,
            ROUND(
                SUM(CASE WHEN criminal_cases > 0 THEN 1 ELSE 0 END) * 100.0
                / NULLIF(COUNT(*), 0), 1
            )                             AS pct_with_cases
        FROM read_parquet('{_silver("disclosure_records.parquet")}')
        GROUP BY election_year, party, state
        ORDER BY election_year, total_criminal_cases DESC
    ) TO '{GOLD_DIR / "criminal_trends.parquet"}'
    (FORMAT PARQUET, COMPRESSION ZSTD);
    """
    con.execute(query)
    out = GOLD_DIR / "criminal_trends.parquet"
    rows = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    return rows, out.stat().st_size


def main() -> None:
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("GOLD LAYER: Analytical aggregates via DuckDB")
    print("=" * 60)
    print(f"Source : {SILVER_DIR}")
    print(f"Target : {GOLD_DIR}")
    print()

    con = duckdb.connect(database=":memory:")

    builders = [
        ("party_performance", build_party_performance),
        ("state_trends", build_state_trends),
        ("wealth_trends", build_wealth_trends),
        ("criminal_trends", build_criminal_trends),
    ]

    total_rows = 0
    total_bytes = 0
    t0 = time.perf_counter()

    for name, fn in builders:
        try:
            rows, size = fn(con)
            total_rows += rows
            total_bytes += size
            print(f"  {name:25s}  {rows:>8,} rows  {size / 1024:>8.1f} KB")
        except Exception as exc:
            print(f"  {name:25s}  ERROR: {exc}")

    elapsed = time.perf_counter() - t0
    print()
    print(f"Total rows  : {total_rows:,}")
    print(f"Total size  : {total_bytes / 1024:.1f} KB ({total_bytes / 1024 / 1024:.2f} MB)")
    print(f"Elapsed     : {elapsed:.2f}s")

    con.close()


if __name__ == "__main__":
    main()
