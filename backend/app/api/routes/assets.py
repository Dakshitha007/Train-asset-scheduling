"""Railway asset REST endpoints."""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from backend.app.database.database import get_db
from backend.app.database.schemas import (
    ApiResponse,
    AssetCreate,
    AssetPage,
    AssetRead,
    AssetUpdate,
    DeleteResult,
)
from backend.app.services import asset_service

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("", response_model=ApiResponse[AssetPage])
def list_assets(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    asset_type: str | None = Query(default=None, min_length=1, max_length=40),
    zone: str | None = Query(default=None, min_length=1, max_length=40),
    db: Session = Depends(get_db),
) -> ApiResponse[AssetPage]:
    items, total = asset_service.list_assets(
        db, limit=limit, offset=offset, asset_type=asset_type, zone=zone
    )
    return ApiResponse(
        message="Assets retrieved.",
        data=AssetPage(
            items=[AssetRead.model_validate(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        ),
    )


@router.post("", response_model=ApiResponse[AssetRead], status_code=status.HTTP_201_CREATED)
def create_asset(
    payload: AssetCreate, db: Session = Depends(get_db)
) -> ApiResponse[AssetRead]:
    asset = asset_service.create_asset(db, payload)
    return ApiResponse(message="Asset created.", data=AssetRead.model_validate(asset))


@router.get("/{asset_id}", response_model=ApiResponse[AssetRead])
def get_asset(
    asset_id: str, db: Session = Depends(get_db)
) -> ApiResponse[AssetRead]:
    asset = asset_service.get_asset(db, asset_id)
    return ApiResponse(message="Asset retrieved.", data=AssetRead.model_validate(asset))


@router.patch("/{asset_id}", response_model=ApiResponse[AssetRead])
def update_asset(
    asset_id: str,
    payload: AssetUpdate,
    db: Session = Depends(get_db),
) -> ApiResponse[AssetRead]:
    asset = asset_service.update_asset(db, asset_id, payload)
    return ApiResponse(message="Asset updated.", data=AssetRead.model_validate(asset))


@router.delete("/{asset_id}", response_model=ApiResponse[DeleteResult])
def delete_asset(
    asset_id: str,
    db: Session = Depends(get_db),
) -> ApiResponse[DeleteResult]:
    asset_service.delete_asset(db, asset_id)
    return ApiResponse(
        message="Asset deleted.", data=DeleteResult(asset_id=asset_id)
    )
