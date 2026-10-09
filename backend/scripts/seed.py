"""Idempotently seed a development database with an admin and sample records.

Required environment variables: ADMIN_PASSWORD. Optional: ADMIN_NAME, ADMIN_EMAIL.
Run after migrations with ``python -m backend.scripts.seed``.
"""

from datetime import date, datetime, timezone
import os

from sqlalchemy import select

from backend.app.database.database import SessionLocal
from backend.app.database.models import (
    AuditLog,
    MaintenanceRequest,
    Prediction,
    RailwayAsset,
    User,
    UserRole,
)

SEED_MODEL_VERSION = "seed-sample-v1"

SAMPLE_ASSETS = (
    {
        "asset_id": "SEED-TRACK-001",
        "asset_type": "Track",
        "station": "STN-001",
        "zone": "West",
        "track_id": "TRACK-001",
        "installation_date": date(2008, 1, 1),
        "asset_age_years": 18.7,
        "last_maintenance_days": 420,
        "inspection_score": 54.0,
        "defect_count": 5,
        "defect_severity": "Medium",
        "previous_failures": 1,
        "train_frequency": 180,
        "axle_load": 22.5,
        "average_speed": 72.0,
        "weather": "Rain",
        "temperature": 27.0,
        "rainfall": 34.0,
        "crew_available": 8,
        "maintenance_duration": 6.0,
        "passenger_peak": True,
        "nearby_alternate_track": True,
        "predicted_failure_probability": 0.68,
        "status": "active",
    },
    {
        "asset_id": "SEED-SIGNAL-002",
        "asset_type": "Signal",
        "station": "STN-014",
        "zone": "North",
        "track_id": "TRACK-014",
        "installation_date": date(2017, 6, 1),
        "asset_age_years": 9.3,
        "last_maintenance_days": 180,
        "inspection_score": 81.0,
        "defect_count": 1,
        "defect_severity": "Low",
        "previous_failures": 0,
        "train_frequency": 95,
        "axle_load": 20.0,
        "average_speed": 88.0,
        "weather": "Sunny",
        "temperature": 24.0,
        "rainfall": 2.0,
        "crew_available": 12,
        "maintenance_duration": 3.0,
        "passenger_peak": False,
        "nearby_alternate_track": True,
        "predicted_failure_probability": 0.22,
        "status": "active",
    },
    {
        "asset_id": "SEED-BRIDGE-003",
        "asset_type": "Bridge",
        "station": "STN-022",
        "zone": "South",
        "track_id": "TRACK-022",
        "installation_date": date(1998, 3, 1),
        "asset_age_years": 28.6,
        "last_maintenance_days": 760,
        "inspection_score": 43.0,
        "defect_count": 7,
        "defect_severity": "High",
        "previous_failures": 2,
        "train_frequency": 130,
        "axle_load": 24.0,
        "average_speed": 55.0,
        "weather": "Fog",
        "temperature": 19.0,
        "rainfall": 8.0,
        "crew_available": 6,
        "maintenance_duration": 8.0,
        "passenger_peak": True,
        "nearby_alternate_track": False,
        "predicted_failure_probability": 0.84,
        "status": "active",
    },
)


def seed_database() -> None:
    """Create one administrator and deterministic sample operational history."""
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password or len(admin_password) < 12:
        raise RuntimeError(
            "Set ADMIN_PASSWORD to a secret of at least 12 characters before seeding."
        )
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com").strip().lower()
    admin_name = os.getenv("ADMIN_NAME", "RailOpt Administrator").strip()

    from pwdlib import PasswordHash

    password_hasher = PasswordHash.recommended()
    with SessionLocal() as session:
        admin = session.scalar(select(User).where(User.email == admin_email))
        if admin is None:
            admin = User(
                name=admin_name,
                email=admin_email,
                password_hash=password_hasher.hash(admin_password),
                role=UserRole.ADMIN.value,
            )
            session.add(admin)
            session.flush()
        elif admin.role != UserRole.ADMIN.value:
            raise RuntimeError(
                "ADMIN_EMAIL already belongs to a non-admin user; choose another seed email."
            )

        assets_by_id: dict[str, RailwayAsset] = {}
        for values in SAMPLE_ASSETS:
            asset = session.get(RailwayAsset, values["asset_id"])
            if asset is None:
                asset = RailwayAsset(**values)
                session.add(asset)
                session.flush()
            assets_by_id[asset.asset_id] = asset

        prediction_samples = {
            "SEED-TRACK-001": (82.0, 0.71),
            "SEED-SIGNAL-002": (48.0, 0.24),
            "SEED-BRIDGE-003": (94.0, 0.88),
        }
        for asset_id, (priority, failure_probability) in prediction_samples.items():
            exists = session.scalar(
                select(Prediction.prediction_id).where(
                    Prediction.asset_id == asset_id,
                    Prediction.model_version == SEED_MODEL_VERSION,
                )
            )
            if exists is None:
                session.add(
                    Prediction(
                        asset_id=asset_id,
                        predicted_priority_score=priority,
                        predicted_failure_probability=failure_probability,
                        model_version=SEED_MODEL_VERSION,
                        prediction_timestamp=datetime.now(timezone.utc),
                    )
                )

        for asset_id, priority in (
            ("SEED-TRACK-001", 82.0),
            ("SEED-BRIDGE-003", 94.0),
        ):
            existing_request = session.scalar(
                select(MaintenanceRequest.request_id).where(
                    MaintenanceRequest.asset_id == asset_id,
                    MaintenanceRequest.preferred_window == "Seed sample window",
                )
            )
            if existing_request is None:
                asset = assets_by_id[asset_id]
                session.add(
                    MaintenanceRequest(
                        asset_id=asset_id,
                        priority=priority,
                        predicted_failure_probability=asset.predicted_failure_probability,
                        maintenance_duration=asset.maintenance_duration,
                        preferred_window="Seed sample window",
                        crew_required=1,
                        status="pending",
                    )
                )

        seed_log_exists = session.scalar(
            select(AuditLog.log_id).where(
                AuditLog.action == "database.seeded",
                AuditLog.entity_id == SEED_MODEL_VERSION,
            )
        )
        if seed_log_exists is None:
            session.add(
                AuditLog(
                    user_id=admin.id,
                    action="database.seeded",
                    entity="seed",
                    entity_id=SEED_MODEL_VERSION,
                    details="Seed administrator and sample railway records verified.",
                )
            )
        session.commit()
    print("Database seed completed. Existing sample assets and predictions were preserved.")


if __name__ == "__main__":
    seed_database()
