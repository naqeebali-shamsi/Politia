"""
Verify GeoJSON constituency boundary files against the Politia database.

Usage:
    python scripts/verify_geojson.py [--db politia_dev.db] [--geojson data/geojson/lok-sabha-constituencies.geojson]
"""

import argparse
import json
import os
import sqlite3
import sys
from collections import defaultdict
from difflib import get_close_matches

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)

DEFAULT_GEOJSON = os.path.join(BACKEND_DIR, "data", "geojson", "lok-sabha-constituencies.geojson")
DEFAULT_DB = os.path.join(BACKEND_DIR, "politia_dev.db")

# Known name mappings: GeoJSON name -> DB name
KNOWN_ALIASES = {
    "ANDAMAN AND NICOBAR ISLANDS": "A&N ISLANDS",
    "DAMAN AND DIU": "DAMAN & DIU",
    "BHANDARA-GONDIYA": "BHANDARA - GONDIYA",
    "RATNAGIRI-SINDHUDURG": "RATNAGIRI - SINDHUDURG",
    "SREERAMPUR": "SERAMPORE",
    "KANYAKUMARI": "KANNIYAKUMARI",
    "FIROZEPUR": "FIROZPUR",
    "MAYILADUTURAI": "MAYILADUTHURAI",
    "THOOTHUKUDI": "THOOTHUKKUDI",
    "ANANTAPURAMU": "ANANTAPUR",
    "ARAKU": "ARAKU VALLEY",
    "BELAGAVI": "BELGAUM",
    "CHIKODI": "CHIKKODI",
    "HAASAN": "HASSAN",
    "BHUVANAGIRI": "BHONGIR",
    "JAYNAGAR": "JAINAGAR",
    "ARAKU": "ARUKU",
}


def load_geojson(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_db_constituencies(db_path: str) -> dict[str, set[str]]:
    """Load constituency names from DB, grouped by state. Returns {name_upper: set(states)}."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Check table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='constituencies'")
    if not cur.fetchone():
        print("ERROR: 'constituencies' table not found in database")
        conn.close()
        return {}

    cur.execute(
        "SELECT DISTINCT UPPER(TRIM(name)), UPPER(TRIM(state)) FROM constituencies WHERE chamber='Lok Sabha'"
    )
    result = defaultdict(set)
    for name, state in cur.fetchall():
        result[name].add(state)
    conn.close()
    return dict(result)


def verify(geojson_path: str, db_path: str):
    print(f"GeoJSON: {geojson_path}")
    print(f"Database: {db_path}")
    print("=" * 70)

    # --- Load GeoJSON ---
    if not os.path.exists(geojson_path):
        print(f"ERROR: GeoJSON file not found: {geojson_path}")
        return

    geo = load_geojson(geojson_path)
    features = geo.get("features", [])
    print(f"\nGeoJSON type: {geo.get('type')}")
    print(f"Total features: {len(features)}")

    if not features:
        print("ERROR: No features found in GeoJSON")
        return

    # Property keys
    props = features[0].get("properties", {})
    print(f"Property keys: {sorted(props.keys())}")

    # Extract constituency names and states
    geo_entries = []
    for feat in features:
        p = feat.get("properties", {})
        name = (p.get("pc_name") or "").strip().upper()
        state = (p.get("st_name") or "").strip().upper()
        geo_entries.append((name, state))

    geo_names = set(e[0] for e in geo_entries)
    print(f"Unique constituency names: {len(geo_names)}")

    # Check for expected count
    if len(features) == 543:
        print("PASS: Feature count matches expected 543 Lok Sabha constituencies")
    else:
        print(f"WARNING: Expected 543 features, got {len(features)}")

    # State distribution
    state_counts = defaultdict(int)
    for _, state in geo_entries:
        state_counts[state] += 1
    print(f"States/UTs represented: {len(state_counts)}")

    # --- Geometry validation ---
    null_geom = sum(1 for f in features if f.get("geometry") is None)
    if null_geom:
        print(f"WARNING: {null_geom} features have null geometry")
    else:
        print("PASS: All features have geometry")

    geom_types = set(f["geometry"]["type"] for f in features if f.get("geometry"))
    print(f"Geometry types: {sorted(geom_types)}")

    # --- Database cross-reference ---
    if not os.path.exists(db_path):
        print(f"\nWARNING: Database not found at {db_path}, skipping cross-reference")
        return

    print("\n" + "=" * 70)
    print("DATABASE CROSS-REFERENCE")
    print("=" * 70)

    db_names = load_db_constituencies(db_path)
    if not db_names:
        return

    db_name_set = set(db_names.keys())
    print(f"DB unique Lok Sabha constituency names: {len(db_name_set)}")

    # Direct matches
    direct_matches = geo_names & db_name_set
    geo_only = geo_names - db_name_set
    db_only = db_name_set - geo_names

    # Apply known aliases
    alias_matched = set()
    for geo_name in list(geo_only):
        alias = KNOWN_ALIASES.get(geo_name)
        if alias and alias in db_name_set:
            alias_matched.add(geo_name)
            geo_only.discard(geo_name)
            db_only.discard(alias)

    total_matched = len(direct_matches) + len(alias_matched)
    match_rate = total_matched / len(geo_names) * 100 if geo_names else 0

    print(f"\nDirect matches: {len(direct_matches)}")
    print(f"Alias matches:  {len(alias_matched)}")
    print(f"Total matched:  {total_matched} / {len(geo_names)}")
    print(f"Match rate:     {match_rate:.1f}%")

    if alias_matched:
        print(f"\n--- Alias-matched ({len(alias_matched)}) ---")
        for name in sorted(alias_matched):
            print(f"  {name}  ->  {KNOWN_ALIASES[name]}")

    if geo_only:
        print(f"\n--- In GeoJSON only ({len(geo_only)}) ---")
        for name in sorted(geo_only):
            close = get_close_matches(name, db_name_set, n=1, cutoff=0.7)
            suggestion = f"  (closest DB match: {close[0]})" if close else ""
            print(f"  {name}{suggestion}")

    if db_only:
        # Filter to likely-current constituencies (exclude obviously historical ones)
        print(f"\n--- In DB only ({len(db_only)} total, showing first 30) ---")
        for name in sorted(db_only)[:30]:
            close = get_close_matches(name, geo_names, n=1, cutoff=0.7)
            suggestion = f"  (closest GeoJSON match: {close[0]})" if close else ""
            print(f"  {name}{suggestion}")
        if len(db_only) > 30:
            print(f"  ... and {len(db_only) - 30} more (likely historical constituencies)")

    # --- Summary ---
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"GeoJSON features:       {len(features)}")
    print(f"GeoJSON unique names:   {len(geo_names)}")
    print(f"DB Lok Sabha names:     {len(db_name_set)}")
    print(f"Match rate:             {match_rate:.1f}%")
    print(f"Unmatched (GeoJSON):    {len(geo_only)}")
    print(f"Unmatched (DB only):    {len(db_only)}")

    if match_rate >= 95:
        print("\nVERDICT: GOOD - GeoJSON data is well-aligned with the database")
    elif match_rate >= 80:
        print("\nVERDICT: FAIR - Some name mapping needed")
    else:
        print("\nVERDICT: POOR - Significant name mismatches, review data sources")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify GeoJSON constituency boundaries")
    parser.add_argument("--geojson", default=DEFAULT_GEOJSON, help="Path to GeoJSON file")
    parser.add_argument("--db", default=DEFAULT_DB, help="Path to SQLite database")
    args = parser.parse_args()

    verify(args.geojson, args.db)
