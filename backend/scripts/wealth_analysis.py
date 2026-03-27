"""
Wealth Anomaly Detection Pipeline for Politia
==============================================
Analyses ~10K disclosure records to find:
  - Statistical outliers (Z-score, IsolationForest)
  - Suspicious wealth growth / drops
  - Criminal + wealth combinations
  - Peer-group anomalies (party, state, year)

Outputs:
  - Console summary tables
  - lakehouse/gold/wealth_anomalies.csv
  - lakehouse/gold/wealth_anomalies.json
"""

import os
import sys
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DB_URL = os.environ.get("POLITIA_DATABASE_URL", "sqlite:///./politia_dev.db")

# Detect database type and create an appropriate engine
if DB_URL.startswith("sqlite"):
    try:
        from sqlalchemy import create_engine as _create_engine
        DB_ENGINE = _create_engine(DB_URL, connect_args={"check_same_thread": False})
    except ImportError:
        print(
            "ERROR: SQLAlchemy is required. Install it with: pip install sqlalchemy",
            file=sys.stderr,
        )
        sys.exit(1)
    DB_IS_SQLITE = True
elif DB_URL.startswith("postgresql") or DB_URL.startswith("postgres"):
    try:
        from sqlalchemy import create_engine as _create_engine
        DB_ENGINE = _create_engine(DB_URL)
        DB_IS_SQLITE = False
    except ImportError:
        print(
            "ERROR: SQLAlchemy is required to connect to PostgreSQL. "
            "Install it with: pip install sqlalchemy psycopg2-binary",
            file=sys.stderr,
        )
        sys.exit(1)
else:
    print("ERROR: Unsupported database URL scheme:", repr(DB_URL), file=sys.stderr)
    print("Set POLITIA_DATABASE_URL to a sqlite:/// or postgresql:// URL.", file=sys.stderr)
    sys.exit(1)
GOLD_DIR = Path(__file__).resolve().parent.parent / "lakehouse" / "gold"
GOLD_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fmt_inr(val):
    """Format a number in Indian Lakhs / Crores notation."""
    if val is None or pd.isna(val):
        return "N/A"
    sign = "-" if val < 0 else ""
    val = abs(val)
    if val >= 1e7:
        return f"{sign}{val / 1e7:,.2f} Cr"
    elif val >= 1e5:
        return f"{sign}{val / 1e5:,.2f} L"
    else:
        return f"{sign}{val:,.0f}"


def print_header(title):
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}")


def print_table(df, max_rows=50):
    with pd.option_context(
        "display.max_rows", max_rows,
        "display.max_columns", 20,
        "display.width", 160,
        "display.max_colwidth", 30,
    ):
        print(df.to_string(index=False))
    print()


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_data():
    with DB_ENGINE.connect() as conn:
        disclosures = pd.read_sql_query("""
            SELECT d.id as disclosure_id,
                   d.politician_id,
                   p.full_name,
                   COALESCE(e.party, p.current_party) as party,
                   p.current_state as state,
                   d.election_year,
                   d.total_assets,
                   d.movable_assets,
                   d.immovable_assets,
                   d.total_liabilities,
                   d.criminal_cases,
                   d.serious_criminal_cases
            FROM disclosure_records d
            JOIN politicians p ON d.politician_id = p.id
            LEFT JOIN election_records e
                ON e.politician_id = d.politician_id
                AND e.election_year = d.election_year
            WHERE d.total_assets IS NOT NULL
              AND d.total_assets > 0
        """, conn)

    # Normalize party names for grouping
    party_map = {
        "Indian National Congress": "INC",
        "INC(I)": "INC",
        "Bharatiya Janata Party": "BJP",
        "BJS": "BJP",
        "Telugu Desam": "TDP",
        "Samajwadi Party": "SP",
        "Bahujan Samaj Party": "BSP",
        "Communist Party Of India (Marxist)": "CPM",
        "Communist Party Of India": "CPI",
        "Indian National Lok Dal": "INLD",
        "All India Anna Dravida Munnetra Kazhagam": "AIADMK",
        "Dravida Munnetra Kazhagam": "DMK",
        "Nationalist Congress Party": "NCP",
        "Aam Aadmi Party": "AAP",
    }
    disclosures["party"] = disclosures["party"].replace(party_map)

    print(f"Loaded {len(disclosures):,} disclosure records")
    print(f"  Unique politicians: {disclosures['politician_id'].nunique():,}")
    print(f"  Election years: {sorted(disclosures['election_year'].unique())}")
    return disclosures


# ---------------------------------------------------------------------------
# 1. Wealth Growth (multi-election filers)
# ---------------------------------------------------------------------------

def compute_wealth_growth(df):
    """For politicians with filings in multiple years, compute growth."""
    multi = df.sort_values(["politician_id", "election_year"])
    multi = multi.groupby("politician_id").filter(lambda g: len(g) > 1)

    records = []
    for pid, grp in multi.groupby("politician_id"):
        grp = grp.sort_values("election_year")
        first = grp.iloc[0]
        last = grp.iloc[-1]
        abs_growth = last["total_assets"] - first["total_assets"]
        pct_growth = (abs_growth / first["total_assets"]) * 100 if first["total_assets"] > 0 else 0
        years_span = last["election_year"] - first["election_year"]
        cagr = ((last["total_assets"] / first["total_assets"]) ** (1 / max(years_span, 1)) - 1) * 100 if first["total_assets"] > 0 else 0

        records.append({
            "politician_id": pid,
            "full_name": last["full_name"],
            "party": last["party"],
            "state": last["state"],
            "first_year": int(first["election_year"]),
            "last_year": int(last["election_year"]),
            "first_assets": first["total_assets"],
            "last_assets": last["total_assets"],
            "abs_growth": abs_growth,
            "pct_growth": pct_growth,
            "cagr": cagr,
            "num_filings": len(grp),
            "criminal_cases_latest": int(last["criminal_cases"] or 0),
        })

    growth_df = pd.DataFrame(records)
    return growth_df


# ---------------------------------------------------------------------------
# 2a. Z-Score Anomaly Detection
# ---------------------------------------------------------------------------

def zscore_anomalies(df, growth_df):
    anomalies = []

    # Per-year, per-party Z-scores on total_assets
    for (year, party), grp in df.groupby(["election_year", "party"]):
        if len(grp) < 5:
            continue
        mean_a = grp["total_assets"].mean()
        std_a = grp["total_assets"].std()
        if std_a == 0:
            continue
        grp = grp.copy()
        grp["zscore_assets"] = (grp["total_assets"] - mean_a) / std_a
        flagged = grp[grp["zscore_assets"].abs() > 3]
        for _, row in flagged.iterrows():
            anomalies.append({
                "type": "zscore_assets_vs_party",
                "politician_id": row["politician_id"],
                "full_name": row["full_name"],
                "party": party,
                "state": row["state"],
                "election_year": int(year),
                "total_assets": row["total_assets"],
                "zscore": round(row["zscore_assets"], 2),
                "party_mean": mean_a,
                "detail": f"Assets {fmt_inr(row['total_assets'])} vs party mean {fmt_inr(mean_a)} (z={row['zscore_assets']:.1f})",
            })

    # Growth Z-scores (across all multi-filers)
    if len(growth_df) > 5:
        mean_g = growth_df["pct_growth"].mean()
        std_g = growth_df["pct_growth"].std()
        if std_g > 0:
            growth_df = growth_df.copy()
            growth_df["zscore_growth"] = (growth_df["pct_growth"] - mean_g) / std_g
            flagged = growth_df[growth_df["zscore_growth"].abs() > 3]
            for _, row in flagged.iterrows():
                anomalies.append({
                    "type": "zscore_growth",
                    "politician_id": row["politician_id"],
                    "full_name": row["full_name"],
                    "party": row["party"],
                    "state": row["state"],
                    "election_year": int(row["last_year"]),
                    "total_assets": row["last_assets"],
                    "zscore": round(row["zscore_growth"], 2),
                    "party_mean": None,
                    "detail": f"Growth {row['pct_growth']:.0f}% ({fmt_inr(row['first_assets'])} -> {fmt_inr(row['last_assets'])}) z={row['zscore_growth']:.1f}",
                })

    return pd.DataFrame(anomalies) if anomalies else pd.DataFrame()


# ---------------------------------------------------------------------------
# 2b. IsolationForest Multi-Dimensional Anomaly Detection
# ---------------------------------------------------------------------------

def isolation_forest_anomalies(df, growth_df):
    # Merge growth info back into latest disclosure per politician
    latest = df.sort_values("election_year").groupby("politician_id").last().reset_index()
    merged = latest.merge(
        growth_df[["politician_id", "abs_growth", "pct_growth"]],
        on="politician_id",
        how="left",
    )
    merged["abs_growth"] = merged["abs_growth"].fillna(0)
    merged["pct_growth"] = merged["pct_growth"].fillna(0)
    merged["criminal_cases"] = merged["criminal_cases"].fillna(0)
    merged["total_liabilities"] = merged["total_liabilities"].fillna(0)

    features = ["total_assets", "total_liabilities", "criminal_cases", "pct_growth", "abs_growth"]
    X = merged[features].copy()

    # Log-transform skewed columns
    for col in ["total_assets", "total_liabilities", "abs_growth"]:
        X[col] = np.log1p(X[col].clip(lower=0))

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    iso = IsolationForest(contamination=0.05, random_state=42, n_estimators=200)
    merged["iso_score"] = iso.fit_predict(X_scaled)
    merged["iso_anomaly_score"] = iso.decision_function(X_scaled)

    anomalies = merged[merged["iso_score"] == -1].copy()
    anomalies = anomalies.sort_values("iso_anomaly_score")

    # Determine what makes each anomalous
    feature_means = X.mean()
    feature_stds = X.std()

    reasons = []
    for _, row in anomalies.iterrows():
        parts = []
        if row["total_assets"] > feature_means["total_assets"] + 2 * feature_stds["total_assets"]:
            parts.append(f"very high assets ({fmt_inr(row['total_assets'])})")
        if row["criminal_cases"] > 3:
            parts.append(f"{int(row['criminal_cases'])} criminal cases")
        if row["pct_growth"] > 500:
            parts.append(f"{row['pct_growth']:.0f}% asset growth")
        if row["pct_growth"] < -50:
            parts.append(f"{row['pct_growth']:.0f}% asset DROP")
        if row["total_liabilities"] > feature_means["total_liabilities"] + 2 * feature_stds["total_liabilities"]:
            parts.append(f"high liabilities ({fmt_inr(row['total_liabilities'])})")
        if not parts:
            parts.append("multi-dimensional outlier")
        reasons.append("; ".join(parts))
    anomalies["anomaly_reason"] = reasons

    return anomalies[["politician_id", "full_name", "party", "state", "election_year",
                       "total_assets", "total_liabilities", "criminal_cases",
                       "pct_growth", "abs_growth", "iso_anomaly_score", "anomaly_reason"]].head(50)


# ---------------------------------------------------------------------------
# 3. Suspicious Patterns
# ---------------------------------------------------------------------------

def suspicious_patterns(df, growth_df):
    results = {}

    # a) Dramatic drops (>80%)
    drops = growth_df[growth_df["pct_growth"] < -80].sort_values("pct_growth")
    drops = drops.copy()
    drops["first_assets_fmt"] = drops["first_assets"].apply(fmt_inr)
    drops["last_assets_fmt"] = drops["last_assets"].apply(fmt_inr)
    results["dramatic_drops"] = drops

    # b) Explosive growth (>1000%)
    explosive = growth_df[growth_df["pct_growth"] > 1000].sort_values("pct_growth", ascending=False)
    explosive = explosive.copy()
    explosive["first_assets_fmt"] = explosive["first_assets"].apply(fmt_inr)
    explosive["last_assets_fmt"] = explosive["last_assets"].apply(fmt_inr)
    results["explosive_growth"] = explosive

    # c) Criminal cases + high wealth (top 20)
    criminal_rich = df[df["criminal_cases"] > 0].copy()
    criminal_rich = criminal_rich.sort_values("election_year").groupby("politician_id").last().reset_index()
    criminal_rich = criminal_rich.sort_values("total_assets", ascending=False).head(20)
    results["criminal_rich"] = criminal_rich

    # d) Zero-asset declarations in the raw data
    with DB_ENGINE.connect() as conn:
        zero_assets = pd.read_sql_query("""
            SELECT d.politician_id, p.full_name,
                   COALESCE(e.party, p.current_party) as party,
                   p.current_state as state,
                   d.election_year, d.total_assets, d.criminal_cases
            FROM disclosure_records d
            JOIN politicians p ON d.politician_id = p.id
            LEFT JOIN election_records e
                ON e.politician_id = d.politician_id
                AND e.election_year = d.election_year
            WHERE (d.total_assets IS NULL OR d.total_assets = 0)
        """, conn)
    results["zero_assets"] = zero_assets

    return results


# ---------------------------------------------------------------------------
# 4. Peer Group Comparison
# ---------------------------------------------------------------------------

def peer_group_analysis(df):
    df = df.copy()

    # Percentile within party
    df["pctl_party"] = df.groupby("party")["total_assets"].rank(pct=True) * 100

    # Percentile within state
    df["pctl_state"] = df.groupby("state")["total_assets"].rank(pct=True) * 100

    # Percentile within election year
    df["pctl_year"] = df.groupby("election_year")["total_assets"].rank(pct=True) * 100

    # Flag >95th percentile in ALL three
    flagged = df[
        (df["pctl_party"] > 95) & (df["pctl_state"] > 95) & (df["pctl_year"] > 95)
    ].copy()
    flagged = flagged.sort_values("total_assets", ascending=False)

    return flagged, df


# ---------------------------------------------------------------------------
# 5. Crorepati Analysis
# ---------------------------------------------------------------------------

def crorepati_analysis(df):
    """Track crorepati share over election years."""
    records = []
    for year, grp in df.groupby("election_year"):
        total = len(grp)
        crorepatis = len(grp[grp["total_assets"] >= 1e7])
        pct = crorepatis / total * 100 if total > 0 else 0
        median_assets = grp["total_assets"].median()
        mean_assets = grp["total_assets"].mean()
        records.append({
            "year": int(year),
            "total_candidates": total,
            "crorepatis": crorepatis,
            "crorepati_pct": round(pct, 1),
            "median_assets": median_assets,
            "mean_assets": mean_assets,
        })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Compile all anomalies for export
# ---------------------------------------------------------------------------

def compile_anomalies(zscore_df, iso_df, growth_df, suspicious, peer_flagged):
    all_rows = []

    # Z-score anomalies
    if not zscore_df.empty:
        for _, row in zscore_df.iterrows():
            all_rows.append({
                "full_name": row["full_name"],
                "party": row["party"],
                "state": row["state"],
                "election_year": row["election_year"],
                "total_assets": row["total_assets"],
                "anomaly_type": row["type"],
                "detail": row["detail"],
                "severity": "HIGH" if abs(row.get("zscore", 0)) > 4 else "MEDIUM",
            })

    # IsolationForest
    if not iso_df.empty:
        for _, row in iso_df.iterrows():
            all_rows.append({
                "full_name": row["full_name"],
                "party": row["party"],
                "state": row["state"],
                "election_year": int(row["election_year"]),
                "total_assets": row["total_assets"],
                "anomaly_type": "isolation_forest",
                "detail": row["anomaly_reason"],
                "severity": "HIGH" if row["iso_anomaly_score"] < -0.15 else "MEDIUM",
            })

    # Explosive growth
    if not suspicious["explosive_growth"].empty:
        for _, row in suspicious["explosive_growth"].iterrows():
            all_rows.append({
                "full_name": row["full_name"],
                "party": row["party"],
                "state": row["state"],
                "election_year": int(row["last_year"]),
                "total_assets": row["last_assets"],
                "anomaly_type": "explosive_growth",
                "detail": f"{row['pct_growth']:.0f}% growth: {row['first_assets_fmt']} -> {row['last_assets_fmt']}",
                "severity": "HIGH",
            })

    # Dramatic drops
    if not suspicious["dramatic_drops"].empty:
        for _, row in suspicious["dramatic_drops"].iterrows():
            all_rows.append({
                "full_name": row["full_name"],
                "party": row["party"],
                "state": row["state"],
                "election_year": int(row["last_year"]),
                "total_assets": row["last_assets"],
                "anomaly_type": "dramatic_drop",
                "detail": f"{row['pct_growth']:.1f}% drop: {row['first_assets_fmt']} -> {row['last_assets_fmt']}",
                "severity": "HIGH",
            })

    # Peer group outliers (de-dup with above)
    if not peer_flagged.empty:
        existing_names = {r["full_name"] for r in all_rows}
        for _, row in peer_flagged.iterrows():
            if row["full_name"] not in existing_names:
                all_rows.append({
                    "full_name": row["full_name"],
                    "party": row["party"],
                    "state": row["state"],
                    "election_year": int(row["election_year"]),
                    "total_assets": row["total_assets"],
                    "anomaly_type": "peer_group_outlier",
                    "detail": f">95th pctl in party ({row['pctl_party']:.0f}%), state ({row['pctl_state']:.0f}%), year ({row['pctl_year']:.0f}%)",
                    "severity": "MEDIUM",
                })

    out = pd.DataFrame(all_rows)
    if not out.empty:
        out = out.drop_duplicates(subset=["full_name", "anomaly_type"]).sort_values(
            ["severity", "total_assets"], ascending=[True, False]
        )
    return out


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    print_header("POLITIA WEALTH ANOMALY DETECTION PIPELINE")
    df = load_data()

    # -----------------------------------------------------------------------
    print_header("CROREPATI TREND OVER ELECTIONS")
    crore_df = crorepati_analysis(df)
    crore_display = crore_df.copy()
    crore_display["median_assets"] = crore_display["median_assets"].apply(fmt_inr)
    crore_display["mean_assets"] = crore_display["mean_assets"].apply(fmt_inr)
    print_table(crore_display)

    # -----------------------------------------------------------------------
    print_header("WEALTH GROWTH ANALYSIS (multi-election filers)")
    growth_df = compute_wealth_growth(df)
    print(f"Politicians with multiple filings: {len(growth_df):,}")
    print()

    # Top 30 by percentage growth
    print("--- TOP 30 BY PERCENTAGE GROWTH ---")
    top_pct = growth_df.sort_values("pct_growth", ascending=False).head(30).copy()
    top_pct["first_assets_fmt"] = top_pct["first_assets"].apply(fmt_inr)
    top_pct["last_assets_fmt"] = top_pct["last_assets"].apply(fmt_inr)
    top_pct["pct_growth_fmt"] = top_pct["pct_growth"].apply(lambda x: f"{x:,.0f}%")
    top_pct["cagr_fmt"] = top_pct["cagr"].apply(lambda x: f"{x:,.1f}%")
    print_table(top_pct[["full_name", "party", "state", "first_year", "last_year",
                          "first_assets_fmt", "last_assets_fmt", "pct_growth_fmt", "cagr_fmt",
                          "criminal_cases_latest"]])

    # Top 30 by absolute growth
    print("--- TOP 30 BY ABSOLUTE GROWTH ---")
    top_abs = growth_df.sort_values("abs_growth", ascending=False).head(30).copy()
    top_abs["first_assets_fmt"] = top_abs["first_assets"].apply(fmt_inr)
    top_abs["last_assets_fmt"] = top_abs["last_assets"].apply(fmt_inr)
    top_abs["abs_growth_fmt"] = top_abs["abs_growth"].apply(fmt_inr)
    top_abs["pct_growth_fmt"] = top_abs["pct_growth"].apply(lambda x: f"{x:,.0f}%")
    print_table(top_abs[["full_name", "party", "state", "first_year", "last_year",
                          "first_assets_fmt", "last_assets_fmt", "abs_growth_fmt", "pct_growth_fmt",
                          "criminal_cases_latest"]])

    # -----------------------------------------------------------------------
    print_header("Z-SCORE ANOMALY DETECTION")
    zscore_df = zscore_anomalies(df, growth_df)
    if not zscore_df.empty:
        print(f"Z-score anomalies found: {len(zscore_df)}")
        print()
        print("--- ASSET Z-SCORE ANOMALIES (vs party mean) ---")
        asset_zs = zscore_df[zscore_df["type"] == "zscore_assets_vs_party"].sort_values("zscore", ascending=False)
        print_table(asset_zs[["full_name", "party", "state", "election_year", "detail"]].head(30))

        growth_zs = zscore_df[zscore_df["type"] == "zscore_growth"]
        if not growth_zs.empty:
            print("--- GROWTH Z-SCORE ANOMALIES ---")
            print_table(growth_zs[["full_name", "party", "state", "election_year", "detail"]].head(20))
    else:
        print("No Z-score anomalies detected.")

    # -----------------------------------------------------------------------
    print_header("ISOLATION FOREST ANOMALY DETECTION (top 50)")
    iso_df = isolation_forest_anomalies(df, growth_df)
    iso_display = iso_df.copy()
    iso_display["total_assets_fmt"] = iso_display["total_assets"].apply(fmt_inr)
    iso_display["liabilities_fmt"] = iso_display["total_liabilities"].apply(fmt_inr)
    iso_display["pct_growth_fmt"] = iso_display["pct_growth"].apply(lambda x: f"{x:,.0f}%")
    print_table(iso_display[["full_name", "party", "state", "election_year",
                              "total_assets_fmt", "liabilities_fmt", "criminal_cases",
                              "pct_growth_fmt", "iso_anomaly_score", "anomaly_reason"]])

    # -----------------------------------------------------------------------
    print_header("SUSPICIOUS PATTERNS")
    suspicious = suspicious_patterns(df, growth_df)

    print(f"\n--- DRAMATIC ASSET DROPS (>80% decline) [{len(suspicious['dramatic_drops'])} found] ---")
    if not suspicious["dramatic_drops"].empty:
        dd = suspicious["dramatic_drops"].copy()
        dd["pct_growth_fmt"] = dd["pct_growth"].apply(lambda x: f"{x:.1f}%")
        print_table(dd[["full_name", "party", "state", "first_year", "last_year",
                         "first_assets_fmt", "last_assets_fmt", "pct_growth_fmt"]].head(20))

    print(f"\n--- EXPLOSIVE GROWTH (>1000%) [{len(suspicious['explosive_growth'])} found] ---")
    if not suspicious["explosive_growth"].empty:
        eg = suspicious["explosive_growth"].copy()
        eg["pct_growth_fmt"] = eg["pct_growth"].apply(lambda x: f"{x:,.0f}%")
        print_table(eg[["full_name", "party", "state", "first_year", "last_year",
                         "first_assets_fmt", "last_assets_fmt", "pct_growth_fmt",
                         "criminal_cases_latest"]].head(30))

    print("\n--- TOP 20 CRIMINAL-CASES + HIGH-WEALTH ---")
    cr = suspicious["criminal_rich"].copy()
    cr["total_assets_fmt"] = cr["total_assets"].apply(fmt_inr)
    print_table(cr[["full_name", "party", "state", "election_year",
                     "total_assets_fmt", "criminal_cases", "serious_criminal_cases"]])

    print(f"\n--- ZERO-ASSET DECLARATIONS [{len(suspicious['zero_assets'])} found] ---")
    za = suspicious["zero_assets"]
    if not za.empty:
        print(f"Total zero/null asset declarations: {len(za)}")
        # Show breakdown by year
        print(za.groupby("election_year").size().to_string())
        print()

    # -----------------------------------------------------------------------
    print_header("PEER GROUP ANALYSIS (>95th pctl in party, state, AND year)")
    peer_flagged, df_with_pctl = peer_group_analysis(df)
    print(f"Politicians flagged: {len(peer_flagged)}")
    if not peer_flagged.empty:
        pf = peer_flagged.copy()
        pf["total_assets_fmt"] = pf["total_assets"].apply(fmt_inr)
        pf["pctl_party"] = pf["pctl_party"].apply(lambda x: f"{x:.0f}")
        pf["pctl_state"] = pf["pctl_state"].apply(lambda x: f"{x:.0f}")
        pf["pctl_year"] = pf["pctl_year"].apply(lambda x: f"{x:.0f}")
        print_table(pf[["full_name", "party", "state", "election_year",
                         "total_assets_fmt", "pctl_party", "pctl_state", "pctl_year"]].head(30))

    # -----------------------------------------------------------------------
    # Export
    # -----------------------------------------------------------------------
    print_header("EXPORTING RESULTS")
    all_anomalies = compile_anomalies(zscore_df, iso_df, growth_df, suspicious, peer_flagged)

    if all_anomalies.empty:
        print("WARNING: No anomalies compiled. Check data.")
        return

    # Format assets for readability in export
    all_anomalies["total_assets_fmt"] = all_anomalies["total_assets"].apply(fmt_inr)

    csv_path = GOLD_DIR / "wealth_anomalies.csv"
    all_anomalies.to_csv(csv_path, index=False)
    print(f"CSV: {csv_path}  ({len(all_anomalies)} rows)")

    json_path = GOLD_DIR / "wealth_anomalies.json"
    # Convert to JSON-safe types
    export = all_anomalies.copy()
    export["total_assets"] = export["total_assets"].astype(float)
    export["election_year"] = export["election_year"].astype(int)
    records = export.to_dict(orient="records")
    with open(json_path, "w") as f:
        json.dump({"anomalies": records, "total_count": len(records)}, f, indent=2, default=str)
    print(f"JSON: {json_path}")

    # -----------------------------------------------------------------------
    # Summary stats
    # -----------------------------------------------------------------------
    print_header("EXECUTIVE SUMMARY")
    print(f"Total disclosure records analysed: {len(df):,}")
    print(f"Multi-election filers tracked: {len(growth_df):,}")
    print(f"Total anomalies detected: {len(all_anomalies):,}")
    print(f"  - HIGH severity: {len(all_anomalies[all_anomalies['severity']=='HIGH']):,}")
    print(f"  - MEDIUM severity: {len(all_anomalies[all_anomalies['severity']=='MEDIUM']):,}")
    print()
    print("Anomaly breakdown by type:")
    print(all_anomalies["anomaly_type"].value_counts().to_string())
    print()
    print("Top 10 most anomalous politicians (by number of flags):")
    top_flagged = all_anomalies.groupby("full_name").size().sort_values(ascending=False).head(10)
    for name, count in top_flagged.items():
        print(f"  {name}: {count} flags")


if __name__ == "__main__":
    main()
