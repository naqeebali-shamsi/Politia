"""
Example DuckDB queries against the gold layer.

Demonstrates sub-millisecond analytical queries on Parquet files --
no database server, no infrastructure cost.
"""
import time
from pathlib import Path

import duckdb

BACKEND_DIR = Path(__file__).resolve().parents[2]
GOLD_DIR = BACKEND_DIR / "lakehouse" / "gold"


def _gold(name: str) -> str:
    return str(GOLD_DIR / name)


def timed_query(con: duckdb.DuckDBPyConnection, title: str, sql: str) -> None:
    """Execute a query, print results with timing."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")

    t0 = time.perf_counter()
    rel = con.execute(sql)
    columns = [desc[0] for desc in rel.description]
    rows = rel.fetchall()
    elapsed_ms = (time.perf_counter() - t0) * 1000

    # Format as table
    col_widths = [max(len(str(c)), max((len(str(row[i])) for row in rows), default=0)) for i, c in enumerate(columns)]
    header = "  ".join(str(c).ljust(w) for c, w in zip(columns, col_widths))
    print(header)
    print("  ".join("-" * w for w in col_widths))
    for row in rows:
        print("  ".join(str(v).ljust(w) for v, w in zip(row, col_widths)))

    print(f"\n  [{elapsed_ms:.1f} ms, {len(rows)} rows]")


def main() -> None:
    con = duckdb.connect(database=":memory:")

    print("LAKEHOUSE QUERY EXAMPLES")
    print("DuckDB in-process, querying Parquet on local disk")
    print("$0 infrastructure cost")

    # ---- Query 1: Top 10 parties by total seats across all elections ----
    timed_query(con, "Top 10 Parties by Seat Count (All Elections)", f"""
        SELECT
            party,
            SUM(seats_won) AS total_seats,
            SUM(candidates) AS total_candidates,
            ROUND(SUM(seats_won) * 100.0 / NULLIF(SUM(candidates), 0), 1) AS overall_win_rate
        FROM read_parquet('{_gold("party_performance.parquet")}')
        GROUP BY party
        ORDER BY total_seats DESC
        LIMIT 10
    """)

    # ---- Query 2: Crorepati trend by year ----
    timed_query(con, "Crorepati Trend by Year", f"""
        SELECT
            election_year,
            total_candidates,
            crorepati_count,
            crorepati_pct || '%' AS crorepati_share,
            CAST(ROUND(avg_assets / 10000000, 1) AS VARCHAR) || ' Cr' AS avg_assets,
            CAST(ROUND(median_assets / 10000000, 1) AS VARCHAR) || ' Cr' AS median_assets
        FROM read_parquet('{_gold("wealth_trends.parquet")}')
        ORDER BY election_year
    """)

    # ---- Query 3: States with highest criminal case rates ----
    timed_query(con, "States with Highest Criminal Case Rates", f"""
        SELECT
            state,
            SUM(total_candidates) AS candidates,
            SUM(candidates_with_cases) AS with_cases,
            ROUND(SUM(candidates_with_cases) * 100.0 / NULLIF(SUM(total_candidates), 0), 1) AS pct_criminal,
            SUM(total_serious_cases) AS serious_cases
        FROM read_parquet('{_gold("criminal_trends.parquet")}')
        WHERE state != 'UNKNOWN'
        GROUP BY state
        HAVING SUM(total_candidates) >= 50
        ORDER BY pct_criminal DESC
        LIMIT 15
    """)

    # ---- Query 4: Election competitiveness over time ----
    timed_query(con, "Election Competitiveness Over Time", f"""
        SELECT
            election_year,
            COUNT(DISTINCT state) AS states,
            SUM(total_seats) AS total_seats,
            ROUND(AVG(avg_winning_margin), 0) AS avg_margin,
            ROUND(AVG(candidates_per_seat), 1) AS avg_candidates_per_seat
        FROM read_parquet('{_gold("state_trends.parquet")}')
        GROUP BY election_year
        ORDER BY election_year
    """)

    # ---- Bonus: Cross-gold join -- parties with most criminal candidates ----
    timed_query(con, "Parties with Most Criminal Candidates (Top 10)", f"""
        SELECT
            c.party,
            SUM(c.candidates_with_cases) AS criminal_candidates,
            SUM(c.total_criminal_cases) AS total_cases,
            p.total_seats
        FROM read_parquet('{_gold("criminal_trends.parquet")}') c
        JOIN (
            SELECT party, SUM(seats_won) AS total_seats
            FROM read_parquet('{_gold("party_performance.parquet")}')
            GROUP BY party
        ) p ON c.party = p.party
        GROUP BY c.party, p.total_seats
        ORDER BY criminal_candidates DESC
        LIMIT 10
    """)

    con.close()
    print("\n" + "=" * 60)
    print("All queries complete.")


if __name__ == "__main__":
    main()
