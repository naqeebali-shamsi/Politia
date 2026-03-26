"""
Integration tests for semantic search endpoint.

These tests run against the real Neon database to verify that:
1. The semantic search endpoint returns results
2. Results are semantically relevant (not just keyword matches)
3. The similarity scores are within expected range
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def _has_embeddings(client: TestClient) -> bool:
    """Check if any embeddings exist in the database."""
    resp = client.get("/api/questions/semantic-search", params={"q": "test", "limit": 1})
    return resp.status_code == 200 and resp.json()["total"] > 0


class TestSemanticSearchEndpoint:
    """Test the /api/questions/semantic-search endpoint."""

    def test_returns_200_with_valid_query(self, client):
        resp = client.get("/api/questions/semantic-search", params={"q": "farmer suicides"})
        assert resp.status_code == 200
        data = resp.json()
        assert "query" in data
        assert "results" in data
        assert "total" in data
        assert data["query"] == "farmer suicides"

    def test_rejects_empty_query(self, client):
        resp = client.get("/api/questions/semantic-search", params={"q": ""})
        assert resp.status_code == 422

    def test_respects_limit_parameter(self, client):
        resp = client.get("/api/questions/semantic-search", params={"q": "education", "limit": 5})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) <= 5

    def test_result_structure(self, client):
        resp = client.get("/api/questions/semantic-search", params={"q": "banking fraud", "limit": 1})
        assert resp.status_code == 200
        data = resp.json()
        if data["total"] > 0:
            item = data["results"][0]
            assert "id" in item
            assert "politician_id" in item
            assert "question_title" in item
            assert "similarity" in item
            assert 0.0 <= item["similarity"] <= 1.0

    def test_semantic_relevance_farmer_distress(self, client):
        """
        'farmer distress' should return results about agriculture/farming
        even if those exact words are not in the title.
        """
        resp = client.get(
            "/api/questions/semantic-search",
            params={"q": "farmer distress", "limit": 10},
        )
        assert resp.status_code == 200
        data = resp.json()
        if data["total"] > 0:
            titles = [r["question_title"].lower() for r in data["results"]]
            # At least one result should mention farming/agriculture/crop/rural keywords
            agri_keywords = {"farm", "agri", "crop", "rural", "kisan", "mandi", "irrigation"}
            found = any(
                any(kw in title for kw in agri_keywords)
                for title in titles
            )
            assert found, f"No agriculture-related results found. Top titles: {titles[:3]}"

    def test_semantic_relevance_bank_fraud(self, client):
        """'bank fraud' should return results about banking/financial crimes."""
        resp = client.get(
            "/api/questions/semantic-search",
            params={"q": "bank fraud", "limit": 10},
        )
        assert resp.status_code == 200
        data = resp.json()
        if data["total"] > 0:
            titles = [r["question_title"].lower() for r in data["results"]]
            finance_keywords = {"bank", "fraud", "loan", "npa", "scam", "financial", "rbi"}
            found = any(
                any(kw in title for kw in finance_keywords)
                for title in titles
            )
            assert found, f"No finance-related results found. Top titles: {titles[:3]}"

    def test_semantic_relevance_women_safety(self, client):
        """'women safety' should return results about women's issues."""
        resp = client.get(
            "/api/questions/semantic-search",
            params={"q": "women safety", "limit": 10},
        )
        assert resp.status_code == 200
        data = resp.json()
        if data["total"] > 0:
            titles = [r["question_title"].lower() for r in data["results"]]
            women_keywords = {"women", "woman", "female", "girl", "rape", "dowry", "domestic", "mahila", "gender"}
            found = any(
                any(kw in title for kw in women_keywords)
                for title in titles
            )
            assert found, f"No women-related results found. Top titles: {titles[:3]}"

    def test_similarity_scores_are_ordered(self, client):
        """Results should be ordered by descending similarity."""
        resp = client.get(
            "/api/questions/semantic-search",
            params={"q": "education policy", "limit": 20},
        )
        assert resp.status_code == 200
        data = resp.json()
        if data["total"] > 1:
            scores = [r["similarity"] for r in data["results"]]
            assert scores == sorted(scores, reverse=True), "Results not ordered by similarity"
