"""Asset persistence and query operations."""

 

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.database.models import Asset, AuditLog
from backend.app.database.schemas import AssetCreate, AssetInput, AssetUpdate


def list_assets(
    db: Session,
    *,
    limit: int,
    offset: int,
    asset_type: str | None = None,
    zone: str | None = None,
) -> tuple[list[Asset], int]:
    """Return a page of assets and the total matching count."""
    filters = []
    if asset_type:
        filters.append(Asset.asset_type == asset_type)
    if zone:
        filters.append(Asset.zone == zone)
    items = db.scalars(
        select(Asset)
        .where(*filters)
        .order_by(Asset.asset_id)
        .offset(offset)
        .limit(limit)
    ).all()
    total = db.scalar(select(func.count()).select_from(Asset).where(*filters)) or 0
    return list(items), int(total)


def get_asset(db: Session, asset_id: str) -> Asset:
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found.")
    return asset


def upsert_asset(db: Session, asset_data: AssetCreate) -> Asset:
    """Insert or refresh the latest known operational record without committing."""
    values = asset_data.model_dump(mode="python")
    asset_id = values.pop("asset_id")
    asset = db.get(Asset, asset_id)
    if asset is None:
        asset = Asset(asset_id=asset_id, **values)
        db.add(asset)
    else:
        for field, value in values.items():
            setattr(asset, field, value)
    db.flush()
    return asset


def create_asset(db: Session, asset_data: AssetCreate) -> Asset:
    if db.get(Asset, asset_data.asset_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An asset with this asset_id already exists.",
        )
    asset = Asset(**asset_data.model_dump(mode="python"))
    db.add(asset)
    db.add(
        AuditLog(
            action="asset.created",
            entity="railway_asset",
            entity_id=asset.asset_id,
        )
    )
    db.commit()
    db.refresh(asset)
    return asset


def update_asset(db: Session, asset_id: str, update: AssetUpdate) -> Asset:
    asset = get_asset(db, asset_id)
    changes = update.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(
            status_code=422,
            detail="Provide at least one field to update.",
        )
    current = {
        field: getattr(asset, field)
        for field in AssetInput.model_fields
    }
    validated = AssetInput.model_validate(current | changes)
    for field, value in validated.model_dump(mode="python").items():
        setattr(asset, field, value)
    db.add(
        AuditLog(
            action="asset.updated",
            entity="railway_asset",
            entity_id=asset.asset_id,
        )
    )
    db.commit()
    db.refresh(asset)
    return asset


def delete_asset(db: Session, asset_id: str) -> None:
    asset = get_asset(db, asset_id)
    db.add(
        AuditLog(
            action="asset.deleted",
            entity="railway_asset",
            entity_id=asset.asset_id,
        )
    )
    db.delete(asset)
    db.commit()
