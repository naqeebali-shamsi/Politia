from fastapi import Depends
from sqlalchemy.orm import Session

from app.infrastructure.database.session import get_db
from app.infrastructure.database.repositories.politician_repository import SqlPoliticianRepository
from app.infrastructure.database.repositories.score_repository import SqlScoreRepository
from app.infrastructure.database.repositories.activity_repository import SqlActivityRepository
from app.infrastructure.database.repositories.disclosure_repository import SqlDisclosureRepository
from app.infrastructure.database.repositories.election_repository import SqlElectionRepository
from app.infrastructure.database.repositories.constituency_repository import SqlConstituencyRepository
from app.infrastructure.database.repositories.source_repository import SqlSourceRepository
from app.domain.interfaces.politician_repository import PoliticianRepository
from app.domain.interfaces.score_repository import ScoreRepository
from app.domain.interfaces.activity_repository import ActivityRepository
from app.domain.interfaces.disclosure_repository import DisclosureRepository
from app.domain.interfaces.election_repository import ElectionRepository
from app.domain.interfaces.constituency_repository import ConstituencyRepository
from app.domain.interfaces.source_repository import SourceRepository
from app.application.services.politician_service import PoliticianService
from app.application.services.leaderboard_service import LeaderboardService
from app.application.services.comparison_service import ComparisonService


# Repository providers — swap implementations here without touching services

def get_politician_repo(db: Session = Depends(get_db)) -> PoliticianRepository:
    return SqlPoliticianRepository(db)


def get_score_repo(db: Session = Depends(get_db)) -> ScoreRepository:
    return SqlScoreRepository(db)


def get_activity_repo(db: Session = Depends(get_db)) -> ActivityRepository:
    return SqlActivityRepository(db)


def get_disclosure_repo(db: Session = Depends(get_db)) -> DisclosureRepository:
    return SqlDisclosureRepository(db)


def get_election_repo(db: Session = Depends(get_db)) -> ElectionRepository:
    return SqlElectionRepository(db)


def get_constituency_repo(db: Session = Depends(get_db)) -> ConstituencyRepository:
    return SqlConstituencyRepository(db)


def get_source_repo(db: Session = Depends(get_db)) -> SourceRepository:
    return SqlSourceRepository(db)


# Service providers

def get_politician_service(
    politician_repo: PoliticianRepository = Depends(get_politician_repo),
    score_repo: ScoreRepository = Depends(get_score_repo),
    activity_repo: ActivityRepository = Depends(get_activity_repo),
    disclosure_repo: DisclosureRepository = Depends(get_disclosure_repo),
    election_repo: ElectionRepository = Depends(get_election_repo),
) -> PoliticianService:
    return PoliticianService(politician_repo, score_repo, activity_repo, disclosure_repo, election_repo)


def get_leaderboard_service(
    politician_repo: PoliticianRepository = Depends(get_politician_repo),
    score_repo: ScoreRepository = Depends(get_score_repo),
) -> LeaderboardService:
    return LeaderboardService(politician_repo, score_repo)


def get_comparison_service(
    politician_repo: PoliticianRepository = Depends(get_politician_repo),
    score_repo: ScoreRepository = Depends(get_score_repo),
    activity_repo: ActivityRepository = Depends(get_activity_repo),
    disclosure_repo: DisclosureRepository = Depends(get_disclosure_repo),
) -> ComparisonService:
    return ComparisonService(politician_repo, score_repo, activity_repo, disclosure_repo)
