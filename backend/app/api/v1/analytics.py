from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_analytics_service
from app.application.services.analytics_service import AnalyticsService
from app.api.schemas.analytics import (
    AnomaliesResponse, AnomalyItem,
    PartyTrendsResponse, PartyTrendItem,
    CrorepatiTrendsResponse, CrorepatiTrendItem,
)

router = APIRouter(tags=["Analytics"])


@router.get("/anomalies", response_model=AnomaliesResponse)
def get_anomalies(
    severity: str | None = None,
    party: str | None = None,
    state: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: AnalyticsService = Depends(get_analytics_service),
):
    result = service.get_anomalies(
        severity=severity, party=party, state=state,
        limit=limit, offset=offset,
    )
    return AnomaliesResponse(
        anomalies=[AnomalyItem(**a) for a in result["anomalies"]],
        total=result["total"],
        offset=result["offset"],
        limit=result["limit"],
        warning=result.get("warning"),
    )


@router.get("/constituencies/{constituency_id}/geojson")
def get_constituency_geojson(
    constituency_id: str,
    service: AnalyticsService = Depends(get_analytics_service),
):
    feature = service.get_constituency_geojson(constituency_id)
    if not feature:
        raise HTTPException(status_code=404, detail="Constituency GeoJSON not found")
    return feature


@router.get("/analytics/party-trends", response_model=PartyTrendsResponse)
def get_party_trends(
    party: str | None = None,
    year: int | None = None,
    service: AnalyticsService = Depends(get_analytics_service),
):
    result = service.get_party_trends(party=party, year=year)
    return PartyTrendsResponse(
        trends=[PartyTrendItem(**t) for t in result["trends"]],
        total=result["total"],
        warning=result.get("warning"),
    )


@router.get("/analytics/crorepati-trends", response_model=CrorepatiTrendsResponse)
def get_crorepati_trends(
    service: AnalyticsService = Depends(get_analytics_service),
):
    result = service.get_crorepati_trends()
    return CrorepatiTrendsResponse(
        trends=[CrorepatiTrendItem(**t) for t in result["trends"]],
        total=result["total"],
        warning=result.get("warning"),
    )
