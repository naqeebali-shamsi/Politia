import json
from pathlib import Path


# Pre-compute paths relative to the backend root
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_GOLD_DIR = _BACKEND_ROOT / "lakehouse" / "gold"
_GEOJSON_DIR = _BACKEND_ROOT / "data" / "geojson"

# Cache loaded data in module-level singletons (loaded once at first request)
_anomalies_cache: dict | None = None
_party_perf_cache: list | None = None
_wealth_trends_cache: list | None = None
_geojson_cache: dict | None = None


def _load_anomalies() -> dict:
    global _anomalies_cache
    if _anomalies_cache is None:
        path = _GOLD_DIR / "wealth_anomalies.json"
        with open(path, encoding="utf-8") as f:
            _anomalies_cache = json.load(f)
    return _anomalies_cache


def _load_party_performance() -> list[dict]:
    global _party_perf_cache
    if _party_perf_cache is None:
        try:
            import polars as pl
            df = pl.read_parquet(_GOLD_DIR / "party_performance.parquet")
            _party_perf_cache = df.to_dicts()
        except Exception:
            _party_perf_cache = []
    return _party_perf_cache


def _load_wealth_trends() -> list[dict]:
    global _wealth_trends_cache
    if _wealth_trends_cache is None:
        try:
            import polars as pl
            df = pl.read_parquet(_GOLD_DIR / "wealth_trends.parquet")
            _wealth_trends_cache = df.to_dicts()
        except Exception:
            _wealth_trends_cache = []
    return _wealth_trends_cache


def _load_geojson() -> dict:
    """Load and index constituency GeoJSON by feature properties."""
    global _geojson_cache
    if _geojson_cache is None:
        _geojson_cache = {}
        geojson_path = _GEOJSON_DIR / "lok-sabha-constituencies.geojson"
        if geojson_path.exists():
            with open(geojson_path, encoding="utf-8") as f:
                data = json.load(f)
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                # Index by multiple keys for flexible lookup
                # Try common GeoJSON property names
                for key in ("pc_id", "PC_ID", "id", "ID", "ST_CODE", "pc_no"):
                    val = props.get(key)
                    if val is not None:
                        _geojson_cache[str(val)] = feature
                # Also index by name for fallback
                for key in ("pc_name", "PC_NAME", "name", "NAME"):
                    val = props.get(key)
                    if val:
                        _geojson_cache[val.upper()] = feature
    return _geojson_cache


class AnalyticsService:
    """Serves pre-computed analytics from the gold layer (JSON/Parquet files)."""

    def get_anomalies(
        self,
        severity: str | None = None,
        party: str | None = None,
        state: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        data = _load_anomalies()
        anomalies = data.get("anomalies", [])

        if severity:
            anomalies = [a for a in anomalies if a.get("severity", "").upper() == severity.upper()]
        if party:
            anomalies = [a for a in anomalies if a.get("party", "").upper() == party.upper()]
        if state:
            anomalies = [a for a in anomalies if a.get("state", "").upper() == state.upper()]

        total = len(anomalies)
        return {
            "anomalies": anomalies[offset: offset + limit],
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    def get_constituency_geojson(self, constituency_id: str) -> dict | None:
        index = _load_geojson()
        # Try direct ID lookup, then uppercase name lookup
        feature = index.get(str(constituency_id))
        if not feature:
            feature = index.get(str(constituency_id).upper())
        return feature

    def get_party_trends(
        self,
        party: str | None = None,
        year: int | None = None,
    ) -> dict:
        records = _load_party_performance()

        filtered = records
        if party:
            filtered = [r for r in filtered if str(r.get("party", "")).upper() == party.upper()]
        if year:
            filtered = [r for r in filtered if r.get("election_year") == year]

        return {
            "trends": filtered,
            "total": len(filtered),
        }

    def get_crorepati_trends(self) -> dict:
        records = _load_wealth_trends()
        return {
            "trends": records,
            "total": len(records),
        }
