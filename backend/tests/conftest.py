import pytest

from tests.fakes import (
    FakePoliticianRepository,
    FakeScoreRepository,
    FakeActivityRepository,
    FakeDisclosureRepository,
    FakeElectionRepository,
    FakeQuestionRepository,
)
from tests.factories import (
    make_politician,
    make_score,
    make_activity,
    make_disclosure,
    make_election,
    make_question,
)


# -- Repository fixtures --

@pytest.fixture
def politician_repo():
    return FakePoliticianRepository()


@pytest.fixture
def score_repo(politician_repo):
    repo = FakeScoreRepository()
    repo.bind_politician_repo(politician_repo)
    return repo


@pytest.fixture
def activity_repo():
    return FakeActivityRepository()


@pytest.fixture
def disclosure_repo():
    return FakeDisclosureRepository()


@pytest.fixture
def election_repo():
    return FakeElectionRepository()


@pytest.fixture
def question_repo():
    return FakeQuestionRepository()


# -- Pre-populated fixtures --

@pytest.fixture
def sample_politicians(politician_repo):
    """Creates 5 sample politicians across different states/parties."""
    politicians = [
        make_politician(full_name="Narendra Modi", current_party="BJP",
                        current_state="Gujarat", current_chamber="Lok Sabha",
                        current_constituency="Varanasi"),
        make_politician(full_name="Rahul Gandhi", current_party="INC",
                        current_state="Kerala", current_chamber="Lok Sabha",
                        current_constituency="Wayanad"),
        make_politician(full_name="Mamata Banerjee", current_party="TMC",
                        current_state="West Bengal", current_chamber="Lok Sabha",
                        current_constituency="Kolkata Dakshin"),
        make_politician(full_name="Amit Shah", current_party="BJP",
                        current_state="Gujarat", current_chamber="Rajya Sabha",
                        current_constituency="Gujarat"),
        make_politician(full_name="Sonia Gandhi", current_party="INC",
                        current_state="Rajasthan", current_chamber="Rajya Sabha",
                        current_constituency="Rajasthan", is_active=False),
    ]
    created = politician_repo.bulk_create(politicians)
    return created


@pytest.fixture
def sample_scores(score_repo, sample_politicians):
    """Creates scores for the sample politicians."""
    scores = []
    for i, p in enumerate(sample_politicians):
        scores.append(make_score(
            politician_id=p.id,
            overall_score=80.0 - i * 5,
            participation_score=75.0 - i * 3,
            disclosure_score=85.0 - i * 2,
            integrity_risk_adjustment=90.0 - i * 5,
        ))
    return score_repo.bulk_create(scores)


@pytest.fixture
def sample_activities(activity_repo, sample_politicians):
    """Creates activity records for sample politicians."""
    activities = []
    for i, p in enumerate(sample_politicians[:3]):  # Only first 3
        activities.append(make_activity(
            politician_id=p.id,
            attendance_percentage=85.0 - i * 10,
            questions_asked=50 - i * 10,
            debates_participated=20 - i * 5,
        ))
    return activity_repo.bulk_create(activities)


@pytest.fixture
def sample_disclosures(disclosure_repo, sample_politicians):
    """Creates disclosure records for sample politicians."""
    disclosures = []
    for i, p in enumerate(sample_politicians[:3]):
        disclosures.append(make_disclosure(
            politician_id=p.id,
            election_year=2024,
            total_assets=50_000_000 + i * 10_000_000,
            criminal_cases=i,
        ))
    return disclosure_repo.bulk_create(disclosures)
