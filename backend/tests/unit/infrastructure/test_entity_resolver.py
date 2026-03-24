"""Tests for entity resolution — name normalization and fuzzy matching."""
import pytest

from app.infrastructure.ingestion.entity_resolver import (
    normalize_name, match_names, find_best_match,
)


class TestNormalizeName:
    def test_strips_shri(self):
        assert normalize_name("Shri Narendra Modi") == "NARENDRA MODI"

    def test_strips_smt(self):
        assert normalize_name("Smt. Sonia Gandhi") == "SONIA GANDHI"

    def test_strips_dr(self):
        assert normalize_name("Dr. Manmohan Singh") == "MANMOHAN SINGH"

    def test_strips_prof(self):
        assert normalize_name("Prof. Ram Gopal Yadav") == "RAM GOPAL YADAV"

    def test_strips_adv(self):
        assert normalize_name("Adv. Prakash Ambedkar") == "PRAKASH AMBEDKAR"

    def test_strips_mr_mrs(self):
        assert normalize_name("Mr. Rajesh Kumar") == "RAJESH KUMAR"
        assert normalize_name("Mrs. Hema Malini") == "HEMA MALINI"

    def test_uppercases(self):
        assert normalize_name("narendra modi") == "NARENDRA MODI"

    def test_collapses_whitespace(self):
        assert normalize_name("  Narendra   Modi  ") == "NARENDRA MODI"

    def test_empty_string(self):
        assert normalize_name("") == ""

    def test_only_title(self):
        assert normalize_name("Shri") == ""

    def test_stacked_titles(self):
        """Multiple titles like 'Shri Dr.' should all be stripped."""
        assert normalize_name("Shri Dr. Rajesh Kumar") == "RAJESH KUMAR"

    def test_stacked_smt_adv(self):
        assert normalize_name("Smt. Adv. Priya Singh") == "PRIYA SINGH"

    def test_no_title(self):
        assert normalize_name("Narendra Modi") == "NARENDRA MODI"

    def test_preserves_middle_names(self):
        assert normalize_name("Shri Rajnath Singh") == "RAJNATH SINGH"

    def test_case_insensitive_title_stripping(self):
        assert normalize_name("SHRI NARENDRA MODI") == "NARENDRA MODI"
        assert normalize_name("smt. sonia gandhi") == "SONIA GANDHI"


class TestMatchNames:
    def test_exact_match(self):
        assert match_names("Narendra Modi", "Narendra Modi") == 100.0

    def test_exact_match_with_titles(self):
        score = match_names("Shri Narendra Modi", "Narendra Modi")
        assert score == 100.0

    def test_reordered_names(self):
        score = match_names("Narendra Modi", "Modi Narendra")
        assert score > 90.0

    def test_completely_different_names(self):
        score = match_names("Narendra Modi", "Rahul Gandhi")
        assert score < 50.0

    def test_similar_names(self):
        score = match_names("Rajnath Singh", "Rajnat Singh")  # Typo
        assert score > 80.0

    def test_empty_strings(self):
        assert match_names("", "") == 100.0  # Both normalized to same empty

    def test_one_empty(self):
        score = match_names("Narendra Modi", "")
        # After normalization, one is empty
        assert score < 50.0

    def test_title_differences_ignored(self):
        score = match_names("Dr. Manmohan Singh", "Shri Manmohan Singh")
        assert score == 100.0

    def test_partial_name(self):
        score = match_names("N. Modi", "Narendra Modi")
        assert score > 50.0  # Partial match

    def test_hindi_transliteration_variants(self):
        """Common spelling variants should still score reasonably."""
        score = match_names("Sharma", "Sharman")
        assert score > 70.0


class TestFindBestMatch:
    def test_finds_exact_match(self):
        candidates = [
            {"full_name": "Narendra Modi", "id": 1},
            {"full_name": "Rahul Gandhi", "id": 2},
        ]
        match = find_best_match("Narendra Modi", candidates)
        assert match is not None
        assert match["id"] == 1

    def test_finds_fuzzy_match_with_lower_threshold(self):
        """Middle names cause lower scores — real-world scenario needs adjusted threshold."""
        candidates = [
            {"full_name": "Narendra Damodardas Modi", "id": 1},
            {"full_name": "Rahul Gandhi", "id": 2},
        ]
        match = find_best_match("Shri Narendra Modi", candidates, threshold=65.0)
        assert match is not None
        assert match["id"] == 1

    def test_finds_close_match_at_default_threshold(self):
        candidates = [
            {"full_name": "Narendra Modi", "id": 1},
            {"full_name": "Rahul Gandhi", "id": 2},
        ]
        match = find_best_match("Shri Narendra Modi", candidates)
        assert match is not None
        assert match["id"] == 1

    def test_returns_none_below_threshold(self):
        candidates = [
            {"full_name": "Rahul Gandhi", "id": 2},
        ]
        match = find_best_match("Narendra Modi", candidates, threshold=90.0)
        assert match is None

    def test_empty_candidates_list(self):
        match = find_best_match("Narendra Modi", [])
        assert match is None

    def test_custom_name_key(self):
        candidates = [
            {"name": "Narendra Modi", "id": 1},
        ]
        match = find_best_match("Narendra Modi", candidates, name_key="name")
        assert match is not None
        assert match["id"] == 1

    def test_picks_best_among_multiple(self):
        candidates = [
            {"full_name": "Rajesh Modi", "id": 1},
            {"full_name": "Narendra Modi", "id": 2},
            {"full_name": "Lalit Modi", "id": 3},
        ]
        match = find_best_match("Narendra Modi", candidates)
        assert match["id"] == 2
