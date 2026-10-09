"""Pydantic v2 request and response schemas."""

from datetime import date, datetime, timedelta

from typing import Any, Generic, Literal, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)

from backend.app.core.constants import (
    ASSET_TYPES,
    DEFECT_SEVERITIES,
    WEATHER_TYPES,
    ZONES,
)

ASSET_STATUSES = ("active", "maintenance", "retired")

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Stable envelope for all successful API responses."""

    success: bool = True
    message: str
    data: T | None = None


class AssetInput(BaseModel):
    """Raw, unscaled asset inputs required by the trained priority model."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    asset_type: str = Field(min_length=1, max_length=40)
    zone: str = Field(min_length=1, max_length=40)
    station: str = Field(min_length=1, max_length=100)
    track_id: str | None = Field(default=None, max_length=100)
    installation_date: date | None = None
    asset_age_years: float = Field(ge=0)
    last_maintenance_days: int = Field(ge=0)
    defect_count: int = Field(ge=0)
    defect_severity: str = Field(min_length=1, max_length=20)
    inspection_score: float = Field(ge=0, le=100)
    train_frequency: int = Field(ge=0)
    average_speed: float = Field(gt=0)
    weather: str = Field(min_length=1, max_length=20)
    temperature: float
    rainfall: float = Field(ge=0)
    axle_load: float = Field(gt=0)
    crew_available: int = Field(ge=0)
    maintenance_duration: float = Field(gt=0)
    passenger_peak: bool
    nearby_alternate_track: bool
    previous_failures: int = Field(ge=0)
    predicted_failure_probability: float = Field(ge=0, le=1)
    status: str = "active"

    @model_validator(mode="after")
    def derive_installation_date(self) -> "AssetInput":
        if self.installation_date is None:
            self.installation_date = date.today() - timedelta(
                days=round(self.asset_age_years * 365.2425)
            )
        return self

    @staticmethod
    def _canonicalize(value: str, allowed: tuple[str, ...], field_name: str) -> str:
        choices = {item.casefold(): item for item in allowed}
        canonical = choices.get(value.strip().casefold())
        if canonical is None:
            raise ValueError(f"{field_name} must be one of: {', '.join(allowed)}")
        return canonical

    @field_validator("asset_type")
    @classmethod
    def validate_asset_type(cls, value: str) -> str:
        return cls._canonicalize(value, ASSET_TYPES, "asset_type")

    @field_validator("zone")
    @classmethod
    def validate_zone(cls, value: str) -> str:
        return cls._canonicalize(value, ZONES, "zone")

    @field_validator("weather")
    @classmethod
    def validate_weather(cls, value: str) -> str:
        return cls._canonicalize(value, WEATHER_TYPES, "weather")

    @field_validator("defect_severity")
    @classmethod
    def validate_defect_severity(cls, value: str) -> str:
        return cls._canonicalize(value, DEFECT_SEVERITIES, "defect_severity")

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ASSET_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(ASSET_STATUSES)}")
        return normalized


class AssetCreate(AssetInput):
    """Create or predict request containing a stable asset identifier."""

    asset_id: str = Field(min_length=1, max_length=100)


class AssetUpdate(BaseModel):
    """Partial asset update; merged data is validated as a full AssetInput."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    asset_type: str | None = None
    zone: str | None = None
    station: str | None = None
    track_id: str | None = None
    installation_date: date | None = None
    asset_age_years: float | None = Field(default=None, ge=0)
    last_maintenance_days: int | None = Field(default=None, ge=0)
    defect_count: int | None = Field(default=None, ge=0)
    defect_severity: str | None = None
    inspection_score: float | None = Field(default=None, ge=0, le=100)
    train_frequency: int | None = Field(default=None, ge=0)
    average_speed: float | None = Field(default=None, gt=0)
    weather: str | None = None
    temperature: float | None = None
    rainfall: float | None = Field(default=None, ge=0)
    axle_load: float | None = Field(default=None, gt=0)
    crew_available: int | None = Field(default=None, ge=0)
    maintenance_duration: float | None = Field(default=None, gt=0)
    passenger_peak: bool | None = None
    nearby_alternate_track: bool | None = None
    previous_failures: int | None = Field(default=None, ge=0)
    predicted_failure_probability: float | None = Field(default=None, ge=0, le=1)
    status: str | None = None


class AssetRead(AssetCreate):
    """Asset resource returned by the asset API."""

    model_config = ConfigDict(from_attributes=True)

    installation_date: date
    created_at: datetime
    updated_at: datetime


class AssetPage(BaseModel):
    """Paginated asset collection."""

    items: list[AssetRead]
    total: int
    limit: int
    offset: int


class DeleteResult(BaseModel):
    """Confirmation payload for resource deletion."""

    asset_id: str
    deleted: bool = True


class PredictionResult(BaseModel):
    """Priority estimate returned by the loaded regression model."""

    asset_id: str
    predicted_priority_score: float
    recommended_action: str
    model_version: str


class PredictionBatchRequest(BaseModel):
    """Bounded prediction batch request."""

    model_config = ConfigDict(extra="forbid")
    assets: list[AssetCreate] = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def unique_asset_ids(self) -> "PredictionBatchRequest":
        asset_ids = [asset.asset_id for asset in self.assets]
        if len(set(asset_ids)) != len(asset_ids):
            raise ValueError("Batch requests must contain unique asset_id values.")
        return self


class OptimizationRequest(BaseModel):
    """Assets and controls supplied to the CP-SAT scheduler."""

    model_config = ConfigDict(extra="forbid")
    assets: list[AssetCreate] = Field(min_length=1, max_length=500)
    available_crews: int = Field(default=8, ge=1, le=100)
    horizon_days: int = Field(default=7, ge=1, le=30)
    priority_threshold: float = Field(default=75, ge=0, le=100)
    critical_priority_threshold: float = Field(default=95, ge=0, le=100)
    planning_start: datetime | None = None

    @model_validator(mode="after")
    def validate_assets_and_thresholds(self) -> "OptimizationRequest":
        asset_ids = [asset.asset_id for asset in self.assets]
        if len(set(asset_ids)) != len(asset_ids):
            raise ValueError("Optimization requests must contain unique asset_id values.")
        if self.critical_priority_threshold < self.priority_threshold:
            raise ValueError(
                "critical_priority_threshold must be greater than or equal to priority_threshold."
            )
        return self


class ScheduleItem(BaseModel):
    """One requested maintenance job and its optimized disposition."""

    maintenance_id: str
    asset_id: str
    asset_type: str
    station: str
    track_id: str | None
    start_time: datetime | None
    end_time: datetime | None
    assigned_crew: str | None
    predicted_priority_score: float
    optimization_score: int
    status: str
    duration_hours: int


class OptimizationMetrics(BaseModel):
    """Operational summary for one optimization run."""

    total_assets_scheduled: int
    request_count: int
    average_delay_hours: float
    asset_availability_percent: float
    crew_utilization_percent: float
    maintenance_completion_percent: float
    estimated_train_impacts: int
    optimization_score: float
    solver_status: str
    solver_seconds: float


class OptimizationResult(BaseModel):
    """Optimized schedule and run metrics."""

    run_id: int
    schedule: list[ScheduleItem]
    metrics: OptimizationMetrics


class HealthStatus(BaseModel):
    """Service and dependency health state."""

    status: str
    model_loaded: bool
    database_connected: bool
    model_version: str | None = None


class DashboardSummary(BaseModel):
    """Headline dashboard KPIs."""

    total_assets: int
    predictions_recorded: int
    mean_priority_score: float | None
    high_priority_assets: int
    latest_optimization_status: str | None
    latest_scheduled_count: int


class DashboardCharts(BaseModel):
    """Chart-ready categorical and time-series aggregates."""

    assets_by_type: list[dict[str, Any]]
    assets_by_zone: list[dict[str, Any]]
    priority_distribution: list[dict[str, Any]]
    schedule_status: list[dict[str, Any]]
    prediction_trend: list[dict[str, Any]]


class UserCreate(BaseModel):
    """User creation payload; plaintext password is never serialized in responses."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: SecretStr = Field(min_length=12, max_length=128)
    role: Literal["Admin", "Planner", "Engineer", "Viewer"] = "Viewer"


class UserRead(BaseModel):
    """Public user fields without password hash or secrets."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: Literal["Admin", "Planner", "Engineer", "Viewer"]
    created_at: datetime
    updated_at: datetime


class MaintenanceRequestRead(BaseModel):
    """Maintenance request with the optional one-to-one optimized disposition."""

    model_config = ConfigDict(from_attributes=True)

    request_id: int
    asset_id: str
    priority: float
    predicted_failure_probability: float
    maintenance_duration: float
    preferred_window: str
    crew_required: int
    status: Literal["pending", "scheduled", "completed", "cancelled"]
    created_at: datetime


class OptimizedScheduleRead(BaseModel):
    """Schedule row persisted for one maintenance request."""

    model_config = ConfigDict(from_attributes=True)

    schedule_id: int
    run_id: int | None
    request_id: int
    assigned_crew: str | None
    maintenance_start: datetime | None
    maintenance_end: datetime | None
    optimization_score: int
    status: Literal["scheduled", "not_scheduled", "completed", "cancelled"]


class AuditLogRead(BaseModel):
    """Audit event payload; password values are never recorded."""

    model_config = ConfigDict(from_attributes=True)

    log_id: int
    user_id: int | None
    action: str
    entity: str
    entity_id: str
    details: str | None
    timestamp: datetime
