from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_comparison_service
from app.application.services.comparison_service import ComparisonService
from app.api.schemas.comparison import CompareRequest, CompareResponse

router = APIRouter(prefix="/compare", tags=["Comparison"])


@router.post("", response_model=CompareResponse)
def compare_politicians(
    request: CompareRequest,
    service: ComparisonService = Depends(get_comparison_service),
):
    try:
        result = service.compare(request.politician_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result
