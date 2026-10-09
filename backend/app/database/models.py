"""Normalized SQLAlchemy 2.x persistence models for the RailOpt AI backend."""

from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from backend.app.database.database import Base


class UserRole(str, Enum):
    ADMIN = "Admin"
    PLANNER = "Planner"
    ENGINEER = "Engineer"
    VIEWER = "Viewer"


class User(Base):
    """Application user; passwords are stored as one-way hashes only."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint(
            "role IN ('Admin', 'Planner', 'Engineer', 'Viewer')",
            name="ck_users_role",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=UserRole.VIEWER.value)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")


class RailwayAsset(Base):
    """Latest operational state for an infrastructure asset."""

    __tablename__ = "railway_assets"
    __table_args__ = (
        CheckConstraint("asset_age_years >= 0", name="ck_railway_assets_age_nonnegative"),
        CheckConstraint(
            "inspection_score >= 0 AND inspection_score <= 100",
            name="ck_railway_assets_inspection_range",
        ),
        CheckConstraint("defect_count >= 0", name="ck_railway_assets_defects_nonnegative"),
        CheckConstraint(
            "previous_failures >= 0", name="ck_railway_assets_failures_nonnegative"
        ),
        CheckConstraint(
            "last_maintenance_days >= 0",
            name="ck_railway_assets_maintenance_days_nonnegative",
        ),
        CheckConstraint("train_frequency >= 0", name="ck_railway_assets_frequency_nonnegative"),
        CheckConstraint("crew_available >= 0", name="ck_railway_assets_crew_nonnegative"),
        CheckConstraint("rainfall >= 0", name="ck_railway_assets_rainfall_nonnegative"),
        CheckConstraint(
            "asset_type IN ('Bridge', 'OHE', 'Signal', 'Switch', 'Track')",
            name="ck_railway_assets_type",
        ),
        CheckConstraint(
            "defect_severity IN ('High', 'Low', 'Medium')",
            name="ck_railway_assets_defect_severity",
        ),
        CheckConstraint("axle_load > 0", name="ck_railway_assets_axle_load_positive"),
        CheckConstraint("average_speed > 0", name="ck_railway_assets_speed_positive"),
        CheckConstraint("maintenance_duration > 0", name="ck_railway_assets_duration_positive"),
        CheckConstraint(
            "predicted_failure_probability >= 0 AND predicted_failure_probability <= 1",
            name="ck_railway_assets_failure_probability_range",
        ),
        CheckConstraint(
            "status IN ('active', 'maintenance', 'retired')",
            name="ck_railway_assets_status",
        ),
        Index("ix_railway_assets_station", "station"),
        Index("ix_railway_assets_zone", "zone"),
        Index("ix_railway_assets_type_zone", "asset_type", "zone"),
    )

    asset_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    asset_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    station: Mapped[str] = mapped_column(String(100), nullable=False)
    zone: Mapped[str] = mapped_column(String(40), nullable=False)
    track_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    installation_date: Mapped[date] = mapped_column(Date, nullable=False)
    asset_age_years: Mapped[float] = mapped_column(Float, nullable=False)
    last_maintenance_days: Mapped[int] = mapped_column(Integer, nullable=False)
    inspection_score: Mapped[float] = mapped_column(Float, nullable=False)
    defect_count: Mapped[int] = mapped_column(Integer, nullable=False)
    defect_severity: Mapped[str] = mapped_column(String(20), nullable=False)
    previous_failures: Mapped[int] = mapped_column(Integer, nullable=False)
    train_frequency: Mapped[int] = mapped_column(Integer, nullable=False)
    axle_load: Mapped[float] = mapped_column(Float, nullable=False)
    average_speed: Mapped[float] = mapped_column(Float, nullable=False)
    weather: Mapped[str] = mapped_column(String(20), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    rainfall: Mapped[float] = mapped_column(Float, nullable=False)
    crew_available: Mapped[int] = mapped_column(Integer, nullable=False)
    maintenance_duration: Mapped[float] = mapped_column(Float, nullable=False)
    passenger_peak: Mapped[bool] = mapped_column(Boolean, nullable=False)
    nearby_alternate_track: Mapped[bool] = mapped_column(Boolean, nullable=False)
    predicted_failure_probability: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="active", server_default="active", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan", passive_deletes=True
    )
    maintenance_requests: Mapped[list["MaintenanceRequest"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan", passive_deletes=True
    )


class Prediction(Base):
    """Append-only model prediction history for an asset."""

    __tablename__ = "predictions"
    __table_args__ = (
        CheckConstraint(
            "predicted_priority_score >= 0 AND predicted_priority_score <= 100",
            name="ck_predictions_priority_range",
        ),
        CheckConstraint(
            "predicted_failure_probability >= 0 AND predicted_failure_probability <= 1",
            name="ck_predictions_failure_probability_range",
        ),
        Index("ix_predictions_asset_id", "asset_id"),
        Index("ix_predictions_asset_timestamp", "asset_id", "prediction_timestamp"),
        Index("ix_predictions_prediction_timestamp", "prediction_timestamp"),
    )

    prediction_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id = synonym("prediction_id")
    asset_id: Mapped[str] = mapped_column(
        ForeignKey("railway_assets.asset_id", ondelete="CASCADE"), nullable=False
    )
    predicted_priority_score: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_failure_probability: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(120), nullable=False)
    prediction_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at = synonym("prediction_timestamp")

    asset: Mapped[RailwayAsset] = relationship(back_populates="predictions")


class OptimizationRun(Base):
    """Optimization execution grouping schedules produced by one solve."""

    __tablename__ = "optimization_runs"
    __table_args__ = (
        CheckConstraint("request_count >= 0", name="ck_optimization_runs_requests_nonnegative"),
        CheckConstraint(
            "scheduled_count >= 0 AND scheduled_count <= request_count",
            name="ck_optimization_runs_scheduled_range",
        ),
        Index("ix_optimization_runs_created_at", "created_at"),
    )

    run_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id = synonym("run_id")
    solver_status: Mapped[str] = mapped_column(String(30), nullable=False)
    objective_score: Mapped[float] = mapped_column(Float, nullable=False)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_count: Mapped[int] = mapped_column(Integer, nullable=False)
    solver_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    schedules: Mapped[list["OptimizedSchedule"]] = relationship(back_populates="run")


class MaintenanceRequest(Base):
    """A user- or optimizer-originated request for maintenance work."""

    __tablename__ = "maintenance_requests"
    __table_args__ = (
        CheckConstraint(
            "priority >= 0 AND priority <= 100",
            name="ck_maintenance_requests_priority_range",
        ),
        CheckConstraint(
            "predicted_failure_probability >= 0 AND predicted_failure_probability <= 1",
            name="ck_maintenance_requests_failure_probability_range",
        ),
        CheckConstraint(
            "maintenance_duration > 0", name="ck_maintenance_requests_duration_positive"
        ),
        CheckConstraint("crew_required >= 1", name="ck_maintenance_requests_crew_positive"),
        CheckConstraint(
            "status IN ('pending', 'scheduled', 'completed', 'cancelled')",
            name="ck_maintenance_requests_status",
        ),
        Index("ix_maintenance_requests_priority", "priority"),
        Index("ix_maintenance_requests_asset_created", "asset_id", "created_at"),
    )

    request_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[str] = mapped_column(
        ForeignKey("railway_assets.asset_id", ondelete="CASCADE"), nullable=False
    )
    priority: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_failure_probability: Mapped[float] = mapped_column(Float, nullable=False)
    maintenance_duration: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_window: Mapped[str] = mapped_column(String(120), nullable=False)
    crew_required: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="pending", server_default="pending"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    asset: Mapped[RailwayAsset] = relationship(back_populates="maintenance_requests")
    schedule: Mapped["OptimizedSchedule | None"] = relationship(
        back_populates="maintenance_request", uselist=False,
        cascade="all, delete-orphan", passive_deletes=True,
    )


class OptimizedSchedule(Base):
    """One optimized scheduling disposition for a maintenance request."""

    __tablename__ = "optimized_schedule"
    __table_args__ = (
        UniqueConstraint("request_id", name="uq_optimized_schedule_request"),
        CheckConstraint(
            "status IN ('scheduled', 'not_scheduled', 'completed', 'cancelled')",
            name="ck_optimized_schedule_status",
        ),
        CheckConstraint(
            "status <> 'scheduled' OR "
            "(maintenance_start IS NOT NULL AND maintenance_end > maintenance_start)",
            name="ck_optimized_schedule_time_order",
        ),
        Index("ix_optimized_schedule_maintenance_start", "maintenance_start"),
    )

    schedule_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int | None] = mapped_column(
        ForeignKey("optimization_runs.run_id", ondelete="SET NULL"), nullable=True, index=True
    )
    request_id: Mapped[int] = mapped_column(
        ForeignKey("maintenance_requests.request_id", ondelete="CASCADE"), nullable=False
    )
    assigned_crew: Mapped[str | None] = mapped_column(String(200), nullable=True)
    maintenance_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    maintenance_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    optimization_score: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)

    maintenance_request: Mapped[MaintenanceRequest] = relationship(back_populates="schedule")
    run: Mapped[OptimizationRun | None] = relationship(back_populates="schedules")


class AuditLog(Base):
    """Append-only audit trail for user and automated system actions."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_entity", "entity", "entity_id"),
        Index("ix_audit_logs_timestamp", "timestamp"),
        Index("ix_audit_logs_user_timestamp", "user_id", "timestamp"),
    )

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(120), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User | None] = relationship(back_populates="audit_logs")


# Import compatibility for the existing API services during the table-name migration.
Asset = RailwayAsset
PredictionRecord = Prediction
MaintenanceSchedule = OptimizedSchedule
