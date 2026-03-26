from fastapi import APIRouter, Depends, Query

from app.dependencies import get_question_service
from app.application.services.question_service import QuestionService
from app.api.schemas.question import (
    QuestionSearchResponse, QuestionItem,
    QuestionStatsResponse, MinistryStatItem, TermStatItem,
)

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.get("", response_model=QuestionSearchResponse)
def search_questions(
    politician_id: int | None = None,
    ministry: str | None = None,
    term: int | None = None,
    q: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: QuestionService = Depends(get_question_service),
):
    result = service.search(
        politician_id=politician_id,
        ministry=ministry,
        term=term,
        query=q,
        offset=offset,
        limit=limit,
    )
    return QuestionSearchResponse(
        results=[
            QuestionItem(
                id=r.id,
                politician_id=r.politician_id,
                term_number=r.term_number,
                question_date=r.question_date,
                ministry=r.ministry,
                question_type=r.question_type,
                question_title=r.question_title,
                source_url=r.source_url,
            )
            for r in result["results"]
        ],
        total=result["total"],
        offset=result["offset"],
        limit=result["limit"],
    )


@router.get("/stats", response_model=QuestionStatsResponse)
def get_question_stats(
    service: QuestionService = Depends(get_question_service),
):
    stats = service.get_stats()
    return QuestionStatsResponse(
        by_ministry=[MinistryStatItem(**s) for s in stats["by_ministry"]],
        by_term=[TermStatItem(**s) for s in stats["by_term"]],
        total=stats["total"],
        ministries=stats["ministries"],
    )
