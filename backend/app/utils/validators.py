"""Reusable model and scheduling input validation."""

from collections.abc import Sequence

import numpy as np
import pandas as pd


class ModelContractError(ValueError):
    """Raised when model artifacts and prepared features do not agree."""


def validate_feature_frame(
    frame: pd.DataFrame, expected_columns: Sequence[str]
) -> pd.DataFrame:
    """Return an ordered numeric matrix or fail before calling the estimator."""
    missing = [column for column in expected_columns if column not in frame.columns]
    if missing:
        raise ModelContractError(f"Prepared model features are missing: {missing}")
    ordered = frame.loc[:, list(expected_columns)].copy()
    non_numeric = ordered.select_dtypes(exclude=np.number).columns.tolist()
    if non_numeric:
        raise ModelContractError(f"Model features must be numeric: {non_numeric}")
    if not np.isfinite(ordered.to_numpy(dtype=float)).all():
        raise ModelContractError("Prepared model features contain non-finite values.")
    return ordered


def validate_prediction_values(values: object, expected_count: int) -> list[float]:
    """Normalize finite scalar predictions and enforce one result per input."""
    predictions = np.asarray(values, dtype=float).reshape(-1)
    if predictions.size != expected_count:
        raise ModelContractError(
            f"Model returned {predictions.size} predictions for {expected_count} assets."
        )
    if not np.isfinite(predictions).all():
        raise ModelContractError("Model returned a non-finite priority score.")
    if np.any((predictions < 0) | (predictions > 100)):
        raise ModelContractError("Model returned a priority score outside [0, 100].")
    return predictions.tolist()
