"""
P0-3 TDD Tests: Entity Resolution Fixes

These tests define the CORRECT behavior that the entity resolver must exhibit.
Written BEFORE implementation — all should FAIL initially, then pass after fixes.
"""
import pytest
from app.infrastructure.ingestion.entity_resolver import normalize_name, match_names


# ============================================================================
# Test 1: Over-merging prevention
# ============================================================================

class TestOverMergingPrevention:
    """Different people with the same name from different places must NOT merge."""

    def test_same_name_different_constituency_not_merged(self):
        """OM PRAKASH from BARABANKI and OM PRAKASH from BILASPUR are different people."""
        # The resolver should have a function that checks whether two records
        # should be merged, considering name + constituency + state
        from app.infrastructure.ingestion.entity_resolver import should_merge

        record_a = {"name": "OM PRAKASH", "constituency": "BARABANKI", "state": "UTTAR PRADESH", "year": 2009}
        record_b = {"name": "OM PRAKASH", "constituency": "BILASPUR", "state": "CHHATTISGARH", "year": 2009}

        assert should_merge(record_a, record_b) is False

    def test_same_name_same_constituency_across_years_merged(self):
        """NARENDRA MODI from VARANASI in 2014 and 2019 IS the same person."""
        from app.infrastructure.ingestion.entity_resolver import should_merge

        record_a = {"name": "NARENDRA MODI", "constituency": "VARANASI", "state": "UTTAR PRADESH", "year": 2014}
        record_b = {"name": "NARENDRA MODI", "constituency": "VARANASI", "state": "UTTAR PRADESH", "year": 2019}

        assert should_merge(record_a, record_b) is True

    def test_same_name_different_state_not_merged(self):
        """RAM KUMAR from UP and RAM KUMAR from BIHAR are different people."""
        from app.infrastructure.ingestion.entity_resolver import should_merge

        record_a = {"name": "RAM KUMAR", "constituency": "GORAKHPUR", "state": "UTTAR PRADESH", "year": 2004}
        record_b = {"name": "RAM KUMAR", "constituency": "PATNA", "state": "BIHAR", "year": 2004}

        assert should_merge(record_a, record_b) is False

    def test_same_name_same_state_different_constituency_same_year_not_merged(self):
        """Two ASHOK KUMARs contesting from different constituencies in UP in the same year."""
        from app.infrastructure.ingestion.entity_resolver import should_merge

        record_a = {"name": "ASHOK KUMAR", "constituency": "MEERUT", "state": "UTTAR PRADESH", "year": 2009}
        record_b = {"name": "ASHOK KUMAR", "constituency": "AGRA", "state": "UTTAR PRADESH", "year": 2009}

        assert should_merge(record_a, record_b) is False

    def test_same_person_different_constituency_across_elections_merged(self):
        """A politician who switches constituencies IS the same person if name+party match closely."""
        from app.infrastructure.ingestion.entity_resolver import should_merge

        # Sonia Gandhi: Amethi 2004, Rae Bareli 2009 — same person, different constituency
        record_a = {"name": "SONIA GANDHI", "constituency": "AMETHI", "state": "UTTAR PRADESH", "year": 1999, "party": "INC"}
        record_b = {"name": "SONIA GANDHI", "constituency": "RAE BARELI", "state": "UTTAR PRADESH", "year": 2004, "party": "INC"}

        # For uncommon names, cross-constituency merge IS correct
        assert should_merge(record_a, record_b) is True


# ============================================================================
# Test 2: Title stripping in stored names
# ============================================================================

class TestTitleStrippingInStorage:
    """Stored politician names should be clean — no DR., SHRI, SMT. prefixes."""

    def test_normalize_strips_all_titles_for_storage(self):
        """Names stored in DB should have titles stripped."""
        from app.infrastructure.ingestion.entity_resolver import clean_name_for_storage

        assert clean_name_for_storage("SHRI NARENDRA MODI") == "NARENDRA MODI"
        assert clean_name_for_storage("DR. MANMOHAN SINGH") == "MANMOHAN SINGH"
        assert clean_name_for_storage("SMT. SONIA GANDHI") == "SONIA GANDHI"
        assert clean_name_for_storage("PROF. RAM GOPAL YADAV") == "RAM GOPAL YADAV"
        assert clean_name_for_storage("ADV. PRAKASH AMBEDKAR") == "PRAKASH AMBEDKAR"
        assert clean_name_for_storage("SHRI DR. RAJESH KUMAR") == "RAJESH KUMAR"

    def test_normalize_preserves_non_title_words(self):
        from app.infrastructure.ingestion.entity_resolver import clean_name_for_storage

        assert clean_name_for_storage("SHRIMAN DAS") == "SHRIMAN DAS"  # SHRIMAN != SHRI
        assert clean_name_for_storage("ADMIRAL VISHNU BHAGWAT") == "ADMIRAL VISHNU BHAGWAT"  # ADMIRAL not a title


# ============================================================================
# Test 3: Temporal plausibility
# ============================================================================

class TestTemporalPlausibility:
    """A 2014 affidavit should NOT match to a politician whose last election was in 1960."""

    def test_reject_match_when_gap_too_large(self):
        """15+ year gap between last election and disclosure = reject."""
        from app.infrastructure.ingestion.entity_resolver import is_temporally_plausible

        assert is_temporally_plausible(last_election_year=1999, disclosure_year=2014) is False
        assert is_temporally_plausible(last_election_year=1962, disclosure_year=2019) is False

    def test_accept_match_within_reasonable_gap(self):
        """Same election cycle or adjacent = accept."""
        from app.infrastructure.ingestion.entity_resolver import is_temporally_plausible

        assert is_temporally_plausible(last_election_year=2009, disclosure_year=2014) is True
        assert is_temporally_plausible(last_election_year=2014, disclosure_year=2014) is True
        assert is_temporally_plausible(last_election_year=2004, disclosure_year=2009) is True

    def test_borderline_gap(self):
        """10 year gap — could be same person contesting after a break."""
        from app.infrastructure.ingestion.entity_resolver import is_temporally_plausible

        assert is_temporally_plausible(last_election_year=2004, disclosure_year=2014) is True
        assert is_temporally_plausible(last_election_year=1999, disclosure_year=2009) is True


# ============================================================================
# Test 4: Name commonality awareness
# ============================================================================

class TestNameCommonality:
    """Common Indian names need stricter matching — require constituency+state match."""

    def test_common_name_requires_constituency_match(self):
        """Names like RAM KUMAR, ASHOK KUMAR, OM PRAKASH need exact constituency match."""
        from app.infrastructure.ingestion.entity_resolver import is_common_name

        assert is_common_name("OM PRAKASH") is True
        assert is_common_name("ASHOK KUMAR") is True
        assert is_common_name("RAM KUMAR") is True
        assert is_common_name("VIJAY KUMAR") is True
        assert is_common_name("RAJESH SINGH") is True

    def test_uncommon_name_allows_fuzzy_match(self):
        """Distinctive names like JYOTIRADITYA SCINDIA can match more loosely."""
        from app.infrastructure.ingestion.entity_resolver import is_common_name

        assert is_common_name("JYOTIRADITYA SCINDIA") is False
        assert is_common_name("PRABODH PANDA") is False
        assert is_common_name("MAMATA BANERJEE") is False


# ============================================================================
# Test 5: Legacy state name mapping
# ============================================================================

class TestLegacyStateMapping:
    """Historical state names should map to modern equivalents."""

    def test_bombay_maps_to_maharashtra(self):
        from app.infrastructure.ingestion.entity_resolver import normalize_state

        assert normalize_state("BOMBAY") == "MAHARASHTRA"

    def test_madras_maps_to_tamil_nadu(self):
        from app.infrastructure.ingestion.entity_resolver import normalize_state

        assert normalize_state("MADRAS") == "TAMIL NADU"

    def test_mysore_maps_to_karnataka(self):
        from app.infrastructure.ingestion.entity_resolver import normalize_state

        assert normalize_state("MYSORE") == "KARNATAKA"

    def test_modern_state_unchanged(self):
        from app.infrastructure.ingestion.entity_resolver import normalize_state

        assert normalize_state("UTTAR PRADESH") == "UTTAR PRADESH"
        assert normalize_state("BIHAR") == "BIHAR"

    def test_pepsu_maps_to_punjab(self):
        from app.infrastructure.ingestion.entity_resolver import normalize_state

        assert normalize_state("PATIALA AND EAST PUNJAB STATES UNION") == "PUNJAB"

    def test_hyderabad_maps_to_andhra(self):
        from app.infrastructure.ingestion.entity_resolver import normalize_state

        assert normalize_state("HYDERABAD") == "ANDHRA PRADESH"

    def test_travancore_cochin_maps_to_kerala(self):
        from app.infrastructure.ingestion.entity_resolver import normalize_state

        assert normalize_state("TRAVANCORE-COCHIN") == "KERALA"
