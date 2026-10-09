"""Startup-loaded model and fitted preprocessing artifacts."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib

from backend.app.core.config import settings
from backend.app.core.constants import CATEGORICAL_FEATURES


@dataclass(frozen=True)
class ModelBundle:
    """In-memory immutable references to one model version and its transforms."""

    model: Any
    feature_columns: tuple[str, ...]
    scaler: Any
    encoders: dict[str, Any]
    model_version: str


def load_model_bundle() -> ModelBundle:
    """Load all deployment artifacts once during application startup."""
    paths = {
        "model": settings.model_path,
        "feature schema": settings.feature_columns_path,
        "scaler": settings.scaler_path,
    }
    paths.update(
        {
            f"encoder {name}": settings.encoders_dir / f"encoder_{name}.joblib"
            for name in CATEGORICAL_FEATURES
        }
    )
    missing = [f"{label}: {path}" for label, path in paths.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Required model artifacts are missing: " + "; ".join(missing))

    model = joblib.load(settings.model_path)
    columns = joblib.load(settings.feature_columns_path)
    scaler = joblib.load(settings.scaler_path)
    encoders = {
        name: joblib.load(settings.encoders_dir / f"encoder_{name}.joblib")
        for name in CATEGORICAL_FEATURES
    }
    feature_columns = tuple(str(column) for column in columns)
    if not feature_columns or len(set(feature_columns)) != len(feature_columns):
        raise ValueError("feature_columns.pkl must contain unique, non-empty feature names.")
    if not callable(getattr(model, "predict", None)):
        raise TypeError("Loaded model does not expose a predict method.")
    if not callable(getattr(scaler, "transform", None)):
        raise TypeError("Loaded scaler does not expose a transform method.")
    for name, encoder in encoders.items():
        if not callable(getattr(encoder, "transform", None)):
            raise TypeError(f"Loaded encoder for '{name}' does not expose transform.")

    return ModelBundle(
        model=model,
        feature_columns=feature_columns,
        scaler=scaler,
        encoders=encoders,
        model_version=Path(settings.model_path).name,
    )
