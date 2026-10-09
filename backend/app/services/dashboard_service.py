"""Database-backed dashboard aggregates."""

from collections import Counter, defaultdict
from datetime import timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.database.models import Asset, MaintenanceSchedule, OptimizationRun, PredictionRecord


def dashboard_summary(db: Session) -> dict[str, object]:
    total_assets = int(db.scalar(select(func.count()).select_from(Asset)) or 0)
    prediction_count = int(
        db.scalar(select(func.count()).select_from(PredictionRecord)) or 0
    )
    mean_priority = db.scalar(select(func.avg(PredictionRecord.predicted_priority_score)))
    high_priority = int(
        db.scalar(
            select(func.count(func.distinct(PredictionRecord.asset_id)))
            .select_from(PredictionRecord)
            .where(PredictionRecord.predicted_priority_score >= 75)
        )
        or 0
    )
    latest_run = db.scalar(
        select(OptimizationRun).order_by(OptimizationRun.created_at.desc()).limit(1)
    )
    return {
        "total_assets": total_assets,
        "predictions_recorded": prediction_count,
        "mean_priority_score": float(mean_priority) if mean_priority is not None else None,
        "high_priority_assets": high_priority,
        "latest_optimization_status": latest_run.solver_status if latest_run else None,
        "latest_scheduled_count": latest_run.scheduled_count if latest_run else 0,
    }


def dashboard_charts(db: Session) -> dict[str, list[dict[str, object]]]:
    assets_by_type = [
        {"label": asset_type, "value": int(count)}
        for asset_type, count in db.execute(
            select(Asset.asset_type, func.count()).group_by(Asset.asset_type).order_by(Asset.asset_type)
        )
    ]
    assets_by_zone = [
        {"label": zone, "value": int(count)}
        for zone, count in db.execute(
            select(Asset.zone, func.count()).group_by(Asset.zone).order_by(Asset.zone)
        )
    ]

    scores = db.scalars(
        select(PredictionRecord.predicted_priority_score)
        .order_by(PredictionRecord.created_at.desc())
        .limit(5000)
    ).all()
    bucket_starts = [min(max(int(float(score) // 10) * 10, 0), 90) for score in scores]
    buckets = Counter(f"{start}-{start + 10}" for start in bucket_starts)
    priority_distribution = [
        {"label": bucket, "value": buckets.get(bucket, 0)}
        for bucket in (f"{start}-{start + 10}" for start in range(0, 100, 10))
    ]

    status_counts = db.execute(
        select(MaintenanceSchedule.status, func.count()).group_by(MaintenanceSchedule.status)
    )
    schedule_status = [
        {"label": status, "value": int(count)} for status, count in status_counts
    ]

    recent_predictions = db.scalars(
        select(PredictionRecord)
        .order_by(PredictionRecord.created_at.desc())
        .limit(1000)
    ).all()
    daily_priorities: dict[str, list[float]] = defaultdict(list)
    for record in recent_predictions:
        created_at = record.created_at
        if created_at.tzinfo is not None:
            created_at = created_at.astimezone(timezone.utc)
        daily_priorities[created_at.date().isoformat()].append(
            float(record.predicted_priority_score)
        )
    prediction_trend = [
        {
            "date": day,
            "mean_priority_score": sum(values) / len(values),
            "count": len(values),
        }
        for day, values in sorted(daily_priorities.items())
    ]
    return {
        "assets_by_type": assets_by_type,
        "assets_by_zone": assets_by_zone,
        "priority_distribution": priority_distribution,
        "schedule_status": schedule_status,
        "prediction_trend": prediction_trend,
    }
