"""Create normalized RailOpt AI operational schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("role IN ('Admin', 'Planner', 'Engineer', 'Viewer')", name="ck_users_role"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    op.create_table(
        "railway_assets",
        sa.Column("asset_id", sa.String(length=100), nullable=False),
        sa.Column("asset_type", sa.String(length=40), nullable=False),
        sa.Column("station", sa.String(length=100), nullable=False),
        sa.Column("zone", sa.String(length=40), nullable=False),
        sa.Column("track_id", sa.String(length=100), nullable=True),
        sa.Column("installation_date", sa.Date(), nullable=False),
        sa.Column("asset_age_years", sa.Float(), nullable=False),
        sa.Column("last_maintenance_days", sa.Integer(), nullable=False),
        sa.Column("inspection_score", sa.Float(), nullable=False),
        sa.Column("defect_count", sa.Integer(), nullable=False),
        sa.Column("defect_severity", sa.String(length=20), nullable=False),
        sa.Column("previous_failures", sa.Integer(), nullable=False),
        sa.Column("train_frequency", sa.Integer(), nullable=False),
        sa.Column("axle_load", sa.Float(), nullable=False),
        sa.Column("average_speed", sa.Float(), nullable=False),
        sa.Column("weather", sa.String(length=20), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("rainfall", sa.Float(), nullable=False),
        sa.Column("crew_available", sa.Integer(), nullable=False),
        sa.Column("maintenance_duration", sa.Float(), nullable=False),
        sa.Column("passenger_peak", sa.Boolean(), nullable=False),
        sa.Column("nearby_alternate_track", sa.Boolean(), nullable=False),
        sa.Column("predicted_failure_probability", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=24), server_default=sa.text("'active'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("asset_age_years >= 0", name="ck_railway_assets_age_nonnegative"),
        sa.CheckConstraint("inspection_score >= 0 AND inspection_score <= 100", name="ck_railway_assets_inspection_range"),
        sa.CheckConstraint("defect_count >= 0", name="ck_railway_assets_defects_nonnegative"),
        sa.CheckConstraint("previous_failures >= 0", name="ck_railway_assets_failures_nonnegative"),
        sa.CheckConstraint("last_maintenance_days >= 0", name="ck_railway_assets_maintenance_days_nonnegative"),
        sa.CheckConstraint("train_frequency >= 0", name="ck_railway_assets_frequency_nonnegative"),
        sa.CheckConstraint("crew_available >= 0", name="ck_railway_assets_crew_nonnegative"),
        sa.CheckConstraint("rainfall >= 0", name="ck_railway_assets_rainfall_nonnegative"),
        sa.CheckConstraint("asset_type IN ('Bridge', 'OHE', 'Signal', 'Switch', 'Track')", name="ck_railway_assets_type"),
        sa.CheckConstraint("defect_severity IN ('High', 'Low', 'Medium')", name="ck_railway_assets_defect_severity"),
        sa.CheckConstraint("axle_load > 0", name="ck_railway_assets_axle_load_positive"),
        sa.CheckConstraint("average_speed > 0", name="ck_railway_assets_speed_positive"),
        sa.CheckConstraint("maintenance_duration > 0", name="ck_railway_assets_duration_positive"),
        sa.CheckConstraint("predicted_failure_probability >= 0 AND predicted_failure_probability <= 1", name="ck_railway_assets_failure_probability_range"),
        sa.CheckConstraint("status IN ('active', 'maintenance', 'retired')", name="ck_railway_assets_status"),
        sa.PrimaryKeyConstraint("asset_id", name="pk_railway_assets"),
    )
    op.create_index("ix_railway_assets_asset_type", "railway_assets", ["asset_type"], unique=False)
    op.create_index("ix_railway_assets_station", "railway_assets", ["station"], unique=False)
    op.create_index("ix_railway_assets_zone", "railway_assets", ["zone"], unique=False)
    op.create_index("ix_railway_assets_track_id", "railway_assets", ["track_id"], unique=False)
    op.create_index("ix_railway_assets_status", "railway_assets", ["status"], unique=False)
    op.create_index("ix_railway_assets_type_zone", "railway_assets", ["asset_type", "zone"], unique=False)

    op.create_table(
        "optimization_runs",
        sa.Column("run_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("solver_status", sa.String(length=30), nullable=False),
        sa.Column("objective_score", sa.Float(), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.Column("scheduled_count", sa.Integer(), nullable=False),
        sa.Column("solver_seconds", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("request_count >= 0", name="ck_optimization_runs_requests_nonnegative"),
        sa.CheckConstraint("scheduled_count >= 0 AND scheduled_count <= request_count", name="ck_optimization_runs_scheduled_range"),
        sa.PrimaryKeyConstraint("run_id", name="pk_optimization_runs"),
    )
    op.create_index("ix_optimization_runs_created_at", "optimization_runs", ["created_at"], unique=False)

    op.create_table(
        "predictions",
        sa.Column("prediction_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("asset_id", sa.String(length=100), nullable=False),
        sa.Column("predicted_priority_score", sa.Float(), nullable=False),
        sa.Column("predicted_failure_probability", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(length=120), nullable=False),
        sa.Column("prediction_timestamp", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("predicted_priority_score >= 0 AND predicted_priority_score <= 100", name="ck_predictions_priority_range"),
        sa.CheckConstraint("predicted_failure_probability >= 0 AND predicted_failure_probability <= 1", name="ck_predictions_failure_probability_range"),
        sa.ForeignKeyConstraint(["asset_id"], ["railway_assets.asset_id"], name="fk_predictions_asset_id_railway_assets", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("prediction_id", name="pk_predictions"),
    )
    op.create_index("ix_predictions_asset_id", "predictions", ["asset_id"], unique=False)
    op.create_index("ix_predictions_asset_timestamp", "predictions", ["asset_id", "prediction_timestamp"], unique=False)
    op.create_index("ix_predictions_prediction_timestamp", "predictions", ["prediction_timestamp"], unique=False)

    op.create_table(
        "maintenance_requests",
        sa.Column("request_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("asset_id", sa.String(length=100), nullable=False),
        sa.Column("priority", sa.Float(), nullable=False),
        sa.Column("predicted_failure_probability", sa.Float(), nullable=False),
        sa.Column("maintenance_duration", sa.Float(), nullable=False),
        sa.Column("preferred_window", sa.String(length=120), nullable=False),
        sa.Column("crew_required", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("priority >= 0 AND priority <= 100", name="ck_maintenance_requests_priority_range"),
        sa.CheckConstraint("predicted_failure_probability >= 0 AND predicted_failure_probability <= 1", name="ck_maintenance_requests_failure_probability_range"),
        sa.CheckConstraint("maintenance_duration > 0", name="ck_maintenance_requests_duration_positive"),
        sa.CheckConstraint("crew_required >= 1", name="ck_maintenance_requests_crew_positive"),
        sa.CheckConstraint("status IN ('pending', 'scheduled', 'completed', 'cancelled')", name="ck_maintenance_requests_status"),
        sa.ForeignKeyConstraint(["asset_id"], ["railway_assets.asset_id"], name="fk_maintenance_requests_asset_id_railway_assets", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("request_id", name="pk_maintenance_requests"),
    )
    op.create_index("ix_maintenance_requests_priority", "maintenance_requests", ["priority"], unique=False)
    op.create_index("ix_maintenance_requests_asset_created", "maintenance_requests", ["asset_id", "created_at"], unique=False)

    op.create_table(
        "optimized_schedule",
        sa.Column("schedule_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=True),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("assigned_crew", sa.String(length=200), nullable=True),
        sa.Column("maintenance_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("maintenance_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("optimization_score", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.CheckConstraint("status IN ('scheduled', 'not_scheduled', 'completed', 'cancelled')", name="ck_optimized_schedule_status"),
        sa.CheckConstraint("status <> 'scheduled' OR (maintenance_start IS NOT NULL AND maintenance_end > maintenance_start)", name="ck_optimized_schedule_time_order"),
        sa.ForeignKeyConstraint(["run_id"], ["optimization_runs.run_id"], name="fk_optimized_schedule_run_id_optimization_runs", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["request_id"], ["maintenance_requests.request_id"], name="fk_optimized_schedule_request_id_maintenance_requests", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("schedule_id", name="pk_optimized_schedule"),
        sa.UniqueConstraint("request_id", name="uq_optimized_schedule_request"),
    )
    op.create_index("ix_optimized_schedule_run_id", "optimized_schedule", ["run_id"], unique=False)
    op.create_index("ix_optimized_schedule_maintenance_start", "optimized_schedule", ["maintenance_start"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("log_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.String(length=120), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_audit_logs_user_id_users", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("log_id", name="pk_audit_logs"),
    )
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity", "entity_id"], unique=False)
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"], unique=False)
    op.create_index("ix_audit_logs_user_timestamp", "audit_logs", ["user_id", "timestamp"], unique=False)


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("optimized_schedule")
    op.drop_table("maintenance_requests")
    op.drop_table("predictions")
    op.drop_table("optimization_runs")
    op.drop_table("railway_assets")
    op.drop_table("users")
