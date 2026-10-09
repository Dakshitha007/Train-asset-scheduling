"""Training and evaluation pipeline for maintenance-priority regression."""

from __future__ import annotations

import json
from time import perf_counter
from typing import Any, Dict, Optional

import joblib
import numpy as np
import pandas as pd

from backend.app.core.constants import CATEGORICAL_FEATURES
from src.config.config import (
    MODEL_OUTPUT_PATH,
    PROCESSED_DATA_DIR,
    RANDOM_STATE,
    REPORT_OUTPUT_PATH,
)
from src.models.evaluate import evaluate_regression_model
from src.utils.logger import get_logger

logger = get_logger(__name__)

TARGET_COLUMN = "priority_score"


class BoundedPriorityRegressor:
    """Expose a fitted regressor while enforcing the API's priority range."""

    def __init__(self, estimator: Any) -> None:
        self.estimator = estimator

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        predictions = np.asarray(self.estimator.predict(features), dtype=float).reshape(-1)
        if not np.isfinite(predictions).all():
            raise ValueError("The priority model produced non-finite predictions.")
        return np.clip(predictions, 0.0, 100.0)


def train_failure_predictor(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    hyperparameters: Optional[Dict[str, Any]] = None,
) -> Any:
    """Train a failure classifier; binary failure labels are not currently supplied."""
    del X_train, y_train, hyperparameters
    raise NotImplementedError(
        "Failure prediction is outside the current priority-regression training stage."
    )


def train_priority_regressor(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    hyperparameters: Optional[Dict[str, Any]] = None,
) -> Any:
    """Train a gradient-boosted tree regressor for maintenance priority."""
    from xgboost import XGBRegressor

    parameters: dict[str, Any] = {
        "n_estimators": 250,
        "max_depth": 6,
        "learning_rate": 0.05,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "tree_method": "hist",
        "objective": "reg:squarederror",
        "n_jobs": -1,
        "random_state": RANDOM_STATE,
        "verbosity": 0,
    }
    parameters.update(hyperparameters or {})
    model = XGBRegressor(**parameters)
    model.fit(X_train, y_train)
    return BoundedPriorityRegressor(model)


def _load_processed_splits() -> tuple[
    dict[str, pd.DataFrame], dict[str, pd.DataFrame], dict[str, pd.Series]
]:
    split_paths = {
        name: PROCESSED_DATA_DIR / f"{name}.csv"
        for name in ("train", "validation", "test")
    }
    missing = [str(path) for path in split_paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Processed dataset files are missing: {missing}")

    datasets = {name: pd.read_csv(path) for name, path in split_paths.items()}
    train_columns = list(datasets["train"].columns)
    if TARGET_COLUMN not in train_columns:
        raise ValueError(f"Processed splits must contain target '{TARGET_COLUMN}'.")

    features: dict[str, pd.DataFrame] = {}
    targets: dict[str, pd.Series] = {}
    for name, dataset in datasets.items():
        if dataset.empty:
            raise ValueError(f"The {name} split is empty.")
        if list(dataset.columns) != train_columns:
            raise ValueError(f"Column names or order differ in {name}.csv.")
        if dataset.isna().any().any():
            raise ValueError(f"Missing values found in {name}.csv.")

        X = dataset.drop(columns=[TARGET_COLUMN])
        y = dataset[TARGET_COLUMN]
        non_numeric = X.select_dtypes(exclude=np.number).columns.tolist()
        if non_numeric:
            raise TypeError(f"Non-numeric features in {name}.csv: {non_numeric}")
        if not np.isfinite(X.to_numpy(dtype=float)).all():
            raise ValueError(f"Non-finite feature values found in {name}.csv.")
        if not np.isfinite(y.to_numpy(dtype=float)).all():
            raise ValueError(f"Non-finite targets found in {name}.csv.")
        if not y.between(0, 100).all():
            raise ValueError(f"Target values in {name}.csv must be in [0, 100].")
        features[name] = X
        targets[name] = y

    return datasets, features, targets


def _load_preprocessing_artifacts(feature_columns: list[str]) -> tuple[Any, dict[str, Any]]:
    scaler_path = MODEL_OUTPUT_PATH / "scaler.pkl"
    encoders_dir = MODEL_OUTPUT_PATH / "encoders"
    encoder_paths = {
        column: encoders_dir / f"encoder_{column}.joblib"
        for column in CATEGORICAL_FEATURES
    }
    missing = [
        str(path)
        for path in [scaler_path, *encoder_paths.values()]
        if not path.is_file()
    ]
    if missing:
        raise FileNotFoundError(
            "Run the existing preprocessing stage before training; missing artifacts: "
            + ", ".join(missing)
        )

    scaler = joblib.load(scaler_path)
    scaler_columns = list(getattr(scaler, "feature_names_in_", ()))
    if not callable(getattr(scaler, "transform", None)) or not scaler_columns:
        raise ValueError("scaler.pkl must be a fitted transformer with named features.")
    encoders = {name: joblib.load(path) for name, path in encoder_paths.items()}
    for name, encoder in encoders.items():
        if not callable(getattr(encoder, "transform", None)) or not hasattr(
            encoder, "classes_"
        ):
            raise ValueError(f"Encoder for '{name}' is not fitted.")
        if "__UNKNOWN__" not in {str(value) for value in encoder.classes_}:
            raise ValueError(
                f"Encoder for '{name}' lacks the backend's __UNKNOWN__ category."
            )

    expected_features = set(scaler_columns) | set(CATEGORICAL_FEATURES)
    if len(expected_features) != len(scaler_columns) + len(CATEGORICAL_FEATURES):
        raise ValueError("Categorical fields must not also appear in scaler features.")
    if set(feature_columns) != expected_features:
        missing_features = sorted(expected_features - set(feature_columns))
        unexpected_features = sorted(set(feature_columns) - expected_features)
        raise ValueError(
            "Processed feature schema does not match the backend preprocessing contract; "
            f"missing={missing_features}, unexpected={unexpected_features}."
        )
    return scaler, encoders


def _candidate_models() -> dict[str, Any]:
    from xgboost import XGBRegressor

    return {
        "Gradient-Boosted Trees": XGBRegressor(
            n_estimators=250,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            tree_method="hist",
            objective="reg:squarederror",
            n_jobs=-1,
            random_state=RANDOM_STATE,
            verbosity=0,
        ),
        "Regularized Linear Booster": XGBRegressor(
            booster="gblinear",
            n_estimators=250,
            learning_rate=0.05,
            reg_lambda=1.0,
            objective="reg:squarederror",
            n_jobs=-1,
            random_state=RANDOM_STATE,
            verbosity=0,
        ),
    }


def run_training_pipeline() -> dict[str, Any]:
    """Compare regressors on validation data, refit the winner, and persist artifacts."""
    _, features, targets = _load_processed_splits()
    feature_columns = features["train"].columns.tolist()
    scaler, encoders = _load_preprocessing_artifacts(feature_columns)
    logger.info(
        "Training priority regressors with %d features; target=%s",
        len(feature_columns),
        TARGET_COLUMN,
    )

    candidate_results: dict[str, dict[str, Any]] = {}
    for name, model in _candidate_models().items():
        started = perf_counter()
        model.fit(features["train"], targets["train"])
        elapsed = perf_counter() - started
        validation_predictions = np.clip(
            model.predict(features["validation"]), 0.0, 100.0
        )
        training_predictions = np.clip(model.predict(features["train"]), 0.0, 100.0)
        validation_metrics = evaluate_regression_model(
            targets["validation"], validation_predictions
        )
        training_metrics = evaluate_regression_model(
            targets["train"], training_predictions
        )
        candidate_results[name] = {
            "training_seconds": elapsed,
            "train": training_metrics,
            "validation": validation_metrics,
        }
        logger.info(
            "%s: validation R2=%.6f RMSE=%.6f (%.2fs)",
            name,
            validation_metrics["r2"],
            validation_metrics["rmse"],
            elapsed,
        )

    selected_name = max(
        candidate_results,
        key=lambda name: (
            candidate_results[name]["validation"]["r2"],
            -candidate_results[name]["validation"]["rmse"],
        ),
    )
    selected_validation_metrics = candidate_results[selected_name]["validation"]
    fit_features = pd.concat(
        [features["train"], features["validation"]], ignore_index=True
    )
    fit_targets = pd.concat(
        [targets["train"], targets["validation"]], ignore_index=True
    )
    estimator = _candidate_models()[selected_name]
    estimator.fit(fit_features, fit_targets)
    final_model = BoundedPriorityRegressor(estimator)
    refit_training_metrics = evaluate_regression_model(
        fit_targets, final_model.predict(fit_features)
    )
    test_metrics = evaluate_regression_model(
        targets["test"], final_model.predict(features["test"])
    )

    MODEL_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_OUTPUT_PATH / "best_model.pkl"
    feature_columns_path = MODEL_OUTPUT_PATH / "feature_columns.pkl"
    joblib.dump(final_model, model_path)
    joblib.dump(feature_columns, feature_columns_path)

    # These fitted transforms are produced by Stage 3 and reused unchanged so
    # backend inference receives the same encodings and scaling as training.
    metrics = {
        "target": TARGET_COLUMN,
        "feature_columns": feature_columns,
        "selected_model": selected_name,
        "selection_metric": "validation R2 (lower validation RMSE breaks ties)",
        "selected_validation_metrics": selected_validation_metrics,
        "refit_train_validation_metrics": refit_training_metrics,
        "test_metrics": test_metrics,
        "candidates": candidate_results,
        "training_data_rows": int(len(features["train"])),
        "validation_data_rows": int(len(features["validation"])),
        "test_data_rows": int(len(features["test"])),
        "refit_train_validation_rows": int(len(fit_features)),
        "preprocessing_artifacts": {
            "scaler": str(MODEL_OUTPUT_PATH / "scaler.pkl"),
            "encoders": {name: str(MODEL_OUTPUT_PATH / "encoders" / f"encoder_{name}.joblib")
                         for name in CATEGORICAL_FEATURES},
        },
    }
    REPORT_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    metrics_path = REPORT_OUTPUT_PATH / "training_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    logger.info("Selected model: %s", selected_name)
    logger.info("Selected validation metrics: %s", selected_validation_metrics)
    logger.info("Held-out test metrics: %s", test_metrics)
    logger.info("Saved model to %s", model_path)
    logger.info("Saved feature schema to %s", feature_columns_path)
    logger.info(
        "Verified preprocessing artifacts: scaler=%s, encoders=%s",
        MODEL_OUTPUT_PATH / "scaler.pkl",
        sorted(encoders),
    )
    logger.info("Saved metrics to %s", metrics_path)
    return metrics


if __name__ == "__main__":
    run_training_pipeline()
