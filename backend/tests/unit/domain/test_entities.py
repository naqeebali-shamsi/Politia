"""Tests for domain entities — verify construction, defaults, and field types."""
import pytest
from datetime import datetime

from app.domain.entities.politician import Politician
from app.domain.entities.score import ScoreRecord
from app.domain.entities.activity import ActivityRecord
from app.domain.entities.disclosure import DisclosureRecord
from app.domain.entities.election import ElectionRecord
from app.domain.entities.constituency import Constituency
from app.domain.entities.office import Office
from app.domain.entities.source import SourceRecord
from app.domain.value_objects.enums import Chamber, ElectionResult, ParseStatus, ConstituencyType


class TestPolitician:
    def test_default_construction(self):
        p = Politician()
        assert p.id is None
        assert p.full_name == ""
        assert p.name_variants == []
        assert p.is_active is True
        assert p.current_party is None

    def test_construction_with_values(self):
        p = Politician(
            id=1, full_name="Narendra Modi",
            current_party="BJP", current_state="Gujarat",
            name_variants=["Modi", "N. Modi"],
        )
        assert p.id == 1
        assert p.full_name == "Narendra Modi"
        assert len(p.name_variants) == 2
        assert p.current_party == "BJP"

    def test_name_variants_are_independent_lists(self):
        """Ensure each Politician gets its own list, not a shared reference."""
        p1 = Politician()
        p2 = Politician()
        p1.name_variants.append("test")
        assert "test" not in p2.name_variants

    def test_cross_source_identifiers(self):
        p = Politician(tcpd_id="TCPD_001", myneta_id="MN_123", prs_slug="narendra-modi")
        assert p.tcpd_id == "TCPD_001"
        assert p.myneta_id == "MN_123"
        assert p.prs_slug == "narendra-modi"


class TestScoreRecord:
    def test_default_construction(self):
        s = ScoreRecord()
        assert s.overall_score == 0.0
        assert s.participation_score == 0.0
        assert s.formula_version == "v1"
        assert s.is_current is True

    def test_construction_with_breakdowns(self):
        s = ScoreRecord(
            politician_id=1, overall_score=75.5,
            participation_breakdown={"attendance": {"score": 85}},
        )
        assert s.participation_breakdown["attendance"]["score"] == 85

    def test_score_ranges(self):
        """Scores should accept any float, validation is in scoring engine."""
        s = ScoreRecord(overall_score=0.0)
        assert s.overall_score == 0.0
        s2 = ScoreRecord(overall_score=100.0)
        assert s2.overall_score == 100.0


class TestActivityRecord:
    def test_default_values(self):
        a = ActivityRecord()
        assert a.questions_asked == 0
        assert a.debates_participated == 0
        assert a.attendance_percentage is None
        assert a.committee_names is None

    def test_with_committee_names(self):
        a = ActivityRecord(committee_names=["Finance", "Defence"])
        assert len(a.committee_names) == 2


class TestDisclosureRecord:
    def test_default_criminal_cases(self):
        d = DisclosureRecord()
        assert d.criminal_cases == 0
        assert d.serious_criminal_cases == 0
        assert d.affidavit_complete is False

    def test_with_financial_data(self):
        d = DisclosureRecord(
            total_assets=50_000_000.0,
            movable_assets=20_000_000.0,
            immovable_assets=30_000_000.0,
            total_liabilities=5_000_000.0,
        )
        assert d.total_assets == 50_000_000.0
        assert d.movable_assets + d.immovable_assets == d.total_assets


class TestElectionRecord:
    def test_default_construction(self):
        e = ElectionRecord()
        assert e.election_year == 0
        assert e.result == ""
        assert e.votes is None

    def test_won_election(self):
        e = ElectionRecord(result="Won", votes=500_000, margin=100_000)
        assert e.result == "Won"
        assert e.margin > 0


class TestConstituency:
    def test_default_construction(self):
        c = Constituency()
        assert c.name == ""
        assert c.geo_data is None

    def test_with_geo_data(self):
        c = Constituency(name="Varanasi", geo_data={"type": "Polygon", "coordinates": []})
        assert c.geo_data["type"] == "Polygon"


class TestOffice:
    def test_default_construction(self):
        o = Office()
        assert o.title == "MP"
        assert o.is_active is True

    def test_with_term_details(self):
        o = Office(chamber="Lok Sabha", party="BJP", term_number=18)
        assert o.term_number == 18


class TestSourceRecord:
    def test_default_construction(self):
        s = SourceRecord()
        assert s.parse_status == "pending"
        assert s.source_name == ""

    def test_with_full_details(self):
        s = SourceRecord(
            source_name="myneta", url="https://myneta.info/candidate/123",
            checksum="abc123", content_type="html",
        )
        assert s.source_name == "myneta"
        assert s.content_type == "html"


class TestEnums:
    def test_chamber_values(self):
        assert Chamber.LOK_SABHA == "Lok Sabha"
        assert Chamber.RAJYA_SABHA == "Rajya Sabha"

    def test_election_result_values(self):
        assert ElectionResult.WON == "Won"
        assert ElectionResult.LOST == "Lost"

    def test_parse_status_values(self):
        assert ParseStatus.PENDING == "pending"
        assert ParseStatus.SUCCESS == "success"
        assert ParseStatus.FAILED == "failed"

    def test_constituency_type_values(self):
        assert ConstituencyType.GENERAL == "General"
        assert ConstituencyType.SC == "SC"
        assert ConstituencyType.ST == "ST"
