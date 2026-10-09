"""Dashboard KPI and chart-data endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database.database import get_db
from backend.app.database.schemas import ApiResponse, DashboardCharts, DashboardSummary
from backend.app.services.dashboard_service import dashboard_charts, dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=ApiResponse[DashboardSummary])
def get_summary(db: Session = Depends(get_db)) -> ApiResponse[DashboardSummary]:
    return ApiResponse(
        message="Dashboard summary retrieved.",
        data=DashboardSummary.model_validate(dashboard_summary(db)),
    )


@router.get("/charts", response_model=ApiResponse[DashboardCharts])
def get_charts(db: Session = Depends(get_db)) -> ApiResponse[DashboardCharts]:
    return ApiResponse(
        message="Dashboard chart data retrieved.",
        data=DashboardCharts.model_validate(dashboard_charts(db)),
    )
