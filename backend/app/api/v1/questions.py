from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dependencies import get_question_service
from app.infrastructure.database.session import get_db
from app.application.services.question_service import QuestionService
from app.api.schemas.question import (
    QuestionSearchResponse, QuestionItem,
    QuestionStatsResponse, MinistryStatItem, TermStatItem,
    SemanticSearchItem, SemanticSearchResponse,
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


@router.get("/semantic-search", response_model=SemanticSearchResponse)
def semantic_search(
    q: str = Query(..., min_length=2, description="Natural language search query"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Semantic similarity search over parliamentary question titles.

    Uses pgvector cosine similarity against pre-computed embeddings from
    paraphrase-multilingual-MiniLM-L12-v2 (384 dimensions).
    Returns the top N most semantically similar questions.
    """
    from app.infrastructure.ml.embedding_model import encode_query

    query_embedding = encode_query(q)
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    rows = db.execute(
        text("""
            SELECT
                id, politician_id, term_number, question_date,
                ministry, question_type, question_title, source_url,
                1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM question_records
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """),
        {"embedding": embedding_str, "limit": limit},
    ).fetchall()

    results = [
        SemanticSearchItem(
            id=r[0],
            politician_id=r[1],
            term_number=r[2],
            question_date=r[3],
            ministry=r[4],
            question_type=r[5],
            question_title=r[6],
            source_url=r[7],
            similarity=round(float(r[8]), 4),
        )
        for r in rows
    ]

    return SemanticSearchResponse(
        query=q,
        results=results,
        total=len(results),
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
