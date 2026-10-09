"""Feature engineering and transformation pipeline for RailOpt AI.

Transforms raw railway asset measurements into predictive domain signals:
- Cumulative Track Stress Indices (Axle Load x Frequency)
- Degradation Accelerators (Asset Age x Defect Severity)
- Environmental Vulnerability Indices (Rainfall & Temperature Extremes)
- Maintenance Urgency Ratios
"""

from typing import Tuple, List, Optional, Any
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Numerical and categorical feature groupings for railway assets
CATEGORICAL_FEATURES: List[str] = [
    "asset_type",
    "zone",
    "station",
    "weather",
    "nearby_alternate_track",
]

NUMERICAL_FEATURES: List[str] = [
    "asset_age_years",
    "last_maintenance_days",
    "defect_count",
    "defect_severity",
    "inspection_score",
    "train_frequency",
    "average_speed",
    "temperature",
    "rainfall",
    "axle_load",
    "crew_available",
    "maintenance_duration",
    "passenger_peak",
    "previous_failures",
]


def extract_track_risk_indices(df: pd.DataFrame) -> pd.DataFrame:
    """Computes domain-specific engineered features from raw asset attributes.

    Args:
        df: Input DataFrame.

    Returns:
        pd.DataFrame: DataFrame enriched with domain feature columns.
    """
    logger.info("Extracting railway domain risk indices...")
    feat_df = df.copy()

    # Track Traffic Load Factor: Cumulative track burden
    if "axle_load" in feat_df.columns and "train_frequency" in feat_df.columns:
        feat_df["track_traffic_burden"] = feat_df["axle_load"] * feat_df["train_frequency"]

    # Defect Pressure Ratio: Defect severity per day since last maintenance
    if "defect_severity" in feat_df.columns and "last_maintenance_days" in feat_df.columns:
        feat_df["defect_pressure_rate"] = feat_df["defect_severity"] / (feat_df["last_maintenance_days"] + 1.0)

    # Weather Exposure Risk: Compound rainfall and temperature stress
    if "rainfall" in feat_df.columns and "temperature" in feat_df.columns:
        feat_df["weather_stress_index"] = (feat_df["rainfall"] / 100.0) * (feat_df["temperature"] / 40.0)

    return feat_df


def build_features_pipeline() -> Any:
    """Builds an industry-standard scikit-learn feature preprocessor.

    Applies one-hot encoding to categorical metadata and standard scaling
    to numerical operational signals.

    Returns:
        Any: Unfitted preprocessor pipeline ready for fitting.
    """
    logger.info("Building scikit-learn feature transformation pipeline...")
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from sklearn.compose import ColumnTransformer

    numeric_transformer = Pipeline(steps=[
        ("scaler", StandardScaler())
    ])

    categorical_transformer = Pipeline(steps=[
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERICAL_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )

    return preprocessor
