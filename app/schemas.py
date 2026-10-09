"""Pydantic data schemas for RailOpt AI REST API endpoints.

Enforces strict input validation and response contracts for railway asset
telemetry and block optimization requests.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class AssetTelemetry(BaseModel):
    """Schema for individual railway asset telemetry records."""
    asset_id: str = Field(..., description="Unique track/asset identifier (e.g. TRK-BLR-001)")
    asset_type: str = Field(..., description="Type of asset (e.g. Track, Signal, Catenary, Point)")
    zone: str = Field(..., description="Railway zone (e.g. SWR, SR, CR, NR)")
    station: str = Field(..., description="Nearest railway station")
    asset_age_years: float = Field(..., ge=0, description="Age of the asset in years")
    last_maintenance_days: int = Field(..., ge=0, description="Days elapsed since last scheduled maintenance")
    defect_count: int = Field(..., ge=0, description="Cumulative number of recorded defects")
    defect_severity: float = Field(..., ge=0, le=10, description="Composite defect severity score (0 to 10)")
    inspection_score: float = Field(..., ge=0, le=100, description="Latest track recording car / manual inspection score")
    train_frequency: int = Field(..., ge=0, description="Average daily train passages")
    average_speed: float = Field(..., ge=0, description="Average section train speed (km/h)")
    weather: str = Field(..., description="Current weather conditions")
    temperature: float = Field(..., description="Ambient temperature (°C)")
    rainfall: float = Field(..., ge=0, description="Precipitation level (mm)")
    axle_load: float = Field(..., ge=0, description="Maximum permitted axle load (tonnes)")
    crew_available: int = Field(..., ge=0, description="Available maintenance personnel count")
    maintenance_duration: float = Field(..., ge=0, description="Estimated hours required for track repair")
    passenger_peak: int = Field(..., description="Indicator of peak passenger traffic (0 or 1)")
    nearby_alternate_track: str = Field(..., description="Availability of detour / alternate track ('Yes' or 'No')")
    previous_failures: int = Field(..., ge=0, description="Historical failure count")


class PredictionResponse(BaseModel):
    """Schema for single asset prediction response."""
    asset_id: str
    predicted_failure_probability: float
    priority_score: float
    recommended_action: str


class OptimizationRequest(BaseModel):
    """Schema for maintenance block scheduling optimization request."""
    max_block_hours: float = Field(default=6.0, gt=0, description="Total block window hours available")
    available_crews: int = Field(default=5, gt=0, description="Available gang/machine crews")
    assets: List[AssetTelemetry] = Field(..., description="List of candidate assets requiring maintenance")


class OptimizationResponse(BaseModel):
    """Schema for maintenance block optimization schedule response."""
    scheduled_blocks: List[dict]
    total_scheduled_hours: float
    crews_utilized: int
    risk_mitigated_score: float
