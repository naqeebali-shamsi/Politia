"""Unit tests for AnalyticsService."""
import json
import pytest
from unittest.mock import patch

from app.application.services.analytics_service import AnalyticsService


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear module-level caches and error list between tests."""
    import app.application.services.analytics_service as mod
    mod._anomalies_cache = None
    mod._party_perf_cache = None
    mod._wealth_trends_cache = None
    mod._geojson_cache = None
    mod._data_load_errors.clear()
    yield
    mod._anomalies_cache = None
    mod._party_perf_cache = None
    mod._wealth_trends_cache = None
    mod._geojson_cache = None
    mod._data_load_errors.clear()


SAMPLE_ANOMALIES = {
    "anomalies": [
        {"full_name": "A", "party": "BJP", "state": "BIHAR", "severity": "HIGH",
         "election_year": 2014, "total_assets": 100.0, "anomaly_type": "zscore",
         "detail": "test", "total_assets_fmt": "1 Cr"},
        {"full_name": "B", "party": "INC", "state": "KARNATAKA", "severity": "MEDIUM",
         "election_year": 2009, "total_assets": 50.0, "anomaly_type": "zscore",
         "detail": "test2", "total_assets_fmt": "0.5 Cr"},
        {"full_name": "C", "party": "BJP", "state": "BIHAR", "severity": "HIGH",
         "election_year": 2019, "total_assets": 200.0, "anomaly_type": "zscore",
         "detail": "test3", "total_assets_fmt": "2 Cr"},
    ],
    "total_count": 3,
}


class TestAnomalies:
    @patch("app.application.services.analytics_service._load_anomalies", return_value=SAMPLE_ANOMALIES)
    def test_get_anomalies_no_filter(self, mock_load):
        service = AnalyticsService()
        result = service.get_anomalies()
        assert result["total"] == 3
        assert len(result["anomalies"]) == 3

    @patch("app.application.services.analytics_service._load_anomalies", return_value=SAMPLE_ANOMALIES)
    def test_get_anomalies_filter_severity(self, mock_load):
        service = AnalyticsService()
        result = service.get_anomalies(severity="HIGH")
        assert result["total"] == 2
        assert all(a["severity"] == "HIGH" for a in result["anomalies"])

    @patch("app.application.services.analytics_service._load_anomalies", return_value=SAMPLE_ANOMALIES)
    def test_get_anomalies_filter_party(self, mock_load):
        service = AnalyticsService()
        result = service.get_anomalies(party="INC")
        assert result["total"] == 1
        assert result["anomalies"][0]["full_name"] == "B"

    @patch("app.application.services.analytics_service._load_anomalies", return_value=SAMPLE_ANOMALIES)
    def test_get_anomalies_pagination(self, mock_load):
        service = AnalyticsService()
        result = service.get_anomalies(offset=1, limit=1)
        assert result["total"] == 3
        assert len(result["anomalies"]) == 1
        assert result["offset"] == 1

    @patch("app.application.services.analytics_service._load_anomalies", return_value=SAMPLE_ANOMALIES)
    def test_get_anomalies_no_warning_when_data_loads(self, mock_load):
        service = AnalyticsService()
        result = service.get_anomalies()
        assert result.get("warning") is None

    def test_get_anomalies_warning_when_load_fails(self):
        """When the data file is missing the response includes a warning key."""
        import app.application.services.analytics_service as mod
        mod._data_load_errors.append("Anomalies data unavailable: [Errno 2] No such file")
        service = AnalyticsService()
        with patch("app.application.services.analytics_service._load_anomalies", return_value={}):
            result = service.get_anomalies()
        assert "warning" in result
        assert result["warning"] is not None


class TestPartyTrends:
    @patch("app.application.services.analytics_service._load_party_performance", return_value=[
        {"election_year": 2014, "party": "BJP", "candidates": 400, "seats_won": 282,
         "total_votes": 170000000, "avg_vote_share": 31.0, "win_rate": 70.5},
        {"election_year": 2014, "party": "INC", "candidates": 420, "seats_won": 44,
         "total_votes": 100000000, "avg_vote_share": 19.3, "win_rate": 10.5},
        {"election_year": 2019, "party": "BJP", "candidates": 436, "seats_won": 303,
         "total_votes": 200000000, "avg_vote_share": 37.4, "win_rate": 69.5},
    ])
    def test_party_trends_filter_by_party(self, mock_load):
        service = AnalyticsService()
        result = service.get_party_trends(party="BJP")
        assert result["total"] == 2
        assert all(t["party"] == "BJP" for t in result["trends"])

    def test_party_trends_warning_when_load_fails(self):
        import app.application.services.analytics_service as mod
        mod._data_load_errors.append("Party performance data unavailable: file missing")
        service = AnalyticsService()
        with patch("app.application.services.analytics_service._load_party_performance", return_value=[]):
            result = service.get_party_trends()
        assert "warning" in result
        assert result["total"] == 0


class TestCrorepatiTrends:
    @patch("app.application.services.analytics_service._load_wealth_trends", return_value=[
        {"election_year": 2009, "total_candidates": 5456, "crorepati_count": 1060,
         "crorepati_pct": 19.4, "avg_assets": None, "median_assets": None,
         "avg_liabilities": None, "avg_movable": None, "avg_immovable": None},
    ])
    def test_crorepati_trends(self, mock_load):
        service = AnalyticsService()
        result = service.get_crorepati_trends()
        assert result["total"] == 1
        assert result["trends"][0]["election_year"] == 2009

    def test_crorepati_trends_warning_when_load_fails(self):
        import app.application.services.analytics_service as mod
        mod._data_load_errors.append("Wealth trends data unavailable: file missing")
        service = AnalyticsService()
        with patch("app.application.services.analytics_service._load_wealth_trends", return_value=[]):
            result = service.get_crorepati_trends()
        assert "warning" in result
        assert result["total"] == 0


class TestDataHealth:
    def test_healthy_when_no_errors(self):
        from app.application.services.analytics_service import get_data_health
        health = get_data_health()
        assert health["healthy"] is True
        assert health["errors"] == []

    def test_unhealthy_when_errors_present(self):
        import app.application.services.analytics_service as mod
        from app.application.services.analytics_service import get_data_health
        mod._data_load_errors.append("test error")
        health = get_data_health()
        assert health["healthy"] is False
        assert len(health["errors"]) == 1
        assert "test error" in health["errors"]

    def test_load_failure_records_error(self):
        """_load_anomalies catching an exception should record an error message."""
        import app.application.services.analytics_service as mod
        from app.application.services.analytics_service import _load_anomalies, get_data_health
        with patch("builtins.open", side_effect=FileNotFoundError("no file")):
            _load_anomalies()
        health = get_data_health()
        assert health["healthy"] is False
        assert any("Anomalies data unavailable" in e for e in health["errors"])
