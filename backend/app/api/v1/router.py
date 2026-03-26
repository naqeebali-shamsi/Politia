from fastapi import APIRouter

from app.api.v1.politicians import router as politicians_router
from app.api.v1.leaderboards import router as leaderboards_router
from app.api.v1.comparisons import router as comparisons_router
from app.api.v1.questions import router as questions_router
from app.api.v1.analytics import router as analytics_router

api_router = APIRouter(prefix="/api")

api_router.include_router(politicians_router)
api_router.include_router(leaderboards_router)
api_router.include_router(comparisons_router)
api_router.include_router(questions_router)
api_router.include_router(analytics_router)
