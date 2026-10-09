"""Apply the fitted Stage 3 transformations to incoming asset telemetry."""

from collections.abc import Sequence

 
import pandas as pd

from backend.app.core.constants import CATEGORICAL_FEATURES
from backend.app.core.model_registry import ModelBundle
from backend.app.database.schemas import AssetCreate
from backend.app.utils.validators import validate_feature_frame


def _categorical_value(column: str, value: object) -> str:
    if column in {"passenger_peak", "nearby_alternate_track"}:
        return "Yes" if bool(value) else "No"
    return str(value)


def prepare_model_features(
    assets: Sequence[AssetCreate], bundle: ModelBundle
) -> pd.DataFrame:
    """Engineer, label-encode, scale, and order one or more raw asset records."""
    if not assets:
        return pd.DataFrame(columns=bundle.feature_columns, dtype=float)

    rows = []
    for asset in assets:
        values = asset.model_dump(mode="python")
        values.pop("asset_id", None)
        values.pop("station", None)
        values.pop("track_id", None)
        values.pop("installation_date", None)
        values.pop("status", None)
        for column in ("passenger_peak", "nearby_alternate_track"):
            values[column] = _categorical_value(column, values[column])
        rows.append(values)
    frame = pd.DataFrame(rows)

    age_days = (frame["asset_age_years"] * 365).clip(lower=1)
    frame["maintenance_overdue_ratio"] = frame["last_maintenance_days"] / age_days
    frame["risk_index"] = (
        frame["defect_count"] * frame["predicted_failure_probability"]
    )
    frame["traffic_load_score"] = frame["train_frequency"] * frame["axle_load"]
    frame["asset_health_score"] = (
        frame["inspection_score"] - frame["defect_count"] * 5
    )
    frame["asset_utilization"] = frame["train_frequency"] / frame["average_speed"].clip(lower=1)

    for column in CATEGORICAL_FEATURES:
        encoder = bundle.encoders[column]
        classes = {str(category) for category in encoder.classes_}
        values = frame[column].map(str)
        unknown_label = "__UNKNOWN__"
        if unknown_label not in classes:
            raise RuntimeError(
                f"Encoder for '{column}' has no {unknown_label!r} class for unseen inputs."
            )
        values = values.where(values.isin(classes), unknown_label)
        frame[column] = encoder.transform(values)

    scaler_columns = list(getattr(bundle.scaler, "feature_names_in_", ()))
    if not scaler_columns:
        raise RuntimeError("The saved scaler does not expose its fitted feature names.")
    missing_scaled = sorted(set(scaler_columns) - set(frame.columns))
    if missing_scaled:
        raise RuntimeError(f"Input preprocessing cannot construct scaler fields: {missing_scaled}")

    scaled = pd.DataFrame(
        bundle.scaler.transform(frame.loc[:, scaler_columns]),
        columns=scaler_columns,
        index=frame.index,
    )
    unscaled = frame.drop(columns=scaler_columns)
    frame = pd.concat([unscaled, scaled], axis=1).reindex(columns=frame.columns)
    return validate_feature_frame(frame, bundle.feature_columns)
