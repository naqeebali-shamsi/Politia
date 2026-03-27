import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _find_backend_root() -> Path:
    """Walk up from this file until we find the directory containing lakehouse/."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "lakehouse").is_dir():
            return current
        current = current.parent
    # Fallback: assume 4 levels up from this file
    return Path(__file__).resolve().parent.parent.parent.parent


_BACKEND_ROOT = _find_backend_root()
_GOLD_DIR = _BACKEND_ROOT / "lakehouse" / "gold"
_GEOJSON_DIR = _BACKEND_ROOT / "data" / "geojson"

logger.info(f"Analytics data root: {_BACKEND_ROOT}")
logger.info(f"Gold dir exists: {_GOLD_DIR.exists()}, GeoJSON dir exists: {_GEOJSON_DIR.exists()}")

# Cache loaded data in module-level singletons (loaded once at first request)
_anomalies_cache: dict | None = None
_party_perf_cache: list | None = None
_wealth_trends_cache: list | None = None
_geojson_cache: dict | None = None

# Accumulates human-readable error messages whenever a data source fails to load.
# Callers can inspect this to distinguish "genuinely empty dataset" from "load failure".
_data_load_errors: list[str] = []


def _load_anomalies() -> dict:
    global _anomalies_cache
    if _anomalies_cache is None:
        path = _GOLD_DIR / "wealth_anomalies.json"
        try:
            with open(path, encoding="utf-8") as f:
                _anomalies_cache = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load anomalies data from {path}: {e}")
            _data_load_errors.append(f"Anomalies data unavailable: {e}")
            _anomalies_cache = {}
    return _anomalies_cache


def _load_party_performance() -> list[dict]:
    global _party_perf_cache
    if _party_perf_cache is None:
        try:
            import polars as pl
            path = _GOLD_DIR / "party_performance.parquet"
            logger.info(f"Loading party performance from {path} (exists={path.exists()})")
            df = pl.read_parquet(path)
            _party_perf_cache = df.to_dicts()
            logger.info(f"Loaded {len(_party_perf_cache)} party performance records")
        except Exception as e:
            logger.warning(f"Failed to load party performance: {e}")
            _data_load_errors.append(f"Party performance data unavailable: {e}")
            _party_perf_cache = []
    return _party_perf_cache


def _load_wealth_trends() -> list[dict]:
    global _wealth_trends_cache
    if _wealth_trends_cache is None:
        try:
            import polars as pl
            path = _GOLD_DIR / "wealth_trends.parquet"
            logger.info(f"Loading wealth trends from {path} (exists={path.exists()})")
            df = pl.read_parquet(path)
            _wealth_trends_cache = df.to_dicts()
            logger.info(f"Loaded {len(_wealth_trends_cache)} wealth trend records")
        except Exception as e:
            logger.warning(f"Failed to load wealth trends: {e}")
            _data_load_errors.append(f"Wealth trends data unavailable: {e}")
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


def get_data_health() -> dict:
    """
    Return a health snapshot for all analytics data sources.

    ``healthy`` is True only when no load errors have been recorded.
    ``errors`` lists each failure message accumulated since process start.
    Call this after at least one request has been served so the caches have
    had a chance to populate (loaders are lazy).
    """
    return {
        "healthy": len(_data_load_errors) == 0,
        "errors": list(_data_load_errors),
    }


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
        result: dict = {
            "anomalies": anomalies[offset: offset + limit],
            "total": total,
            "offset": offset,
            "limit": limit,
        }
        if _data_load_errors:
            result["warning"] = "Some analytics data failed to load: " + "; ".join(_data_load_errors)
        return result

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

        result: dict = {
            "trends": filtered,
            "total": len(filtered),
        }
        if _data_load_errors:
            result["warning"] = "Some analytics data failed to load: " + "; ".join(_data_load_errors)
        return result

    def get_crorepati_trends(self) -> dict:
        records = _load_wealth_trends()
        result: dict = {
            "trends": records,
            "total": len(records),
        }
        if _data_load_errors:
            result["warning"] = "Some analytics data failed to load: " + "; ".join(_data_load_errors)
        return result
