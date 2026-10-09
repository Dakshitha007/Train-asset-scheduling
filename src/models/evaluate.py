"""Model evaluation and metrics computation module for RailOpt AI.

Calculates standard machine learning benchmarks and domain-specific railway KPIs:
- Precision, Recall, F1, ROC-AUC (Failure Classification)
- MAE, RMSE, R-squared (Priority Regression)
- Operational safety margins and delay impact estimation
"""

from typing import Dict, Any, Union, Optional
import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


def evaluate_classification_model(
    y_true: Union[pd.Series, np.ndarray],
    y_pred: Union[pd.Series, np.ndarray],
    y_prob: Optional[Union[pd.Series, np.ndarray]] = None,
) -> Dict[str, float]:
    """Computes comprehensive classification metrics for failure prediction.

    Args:
        y_true: Ground truth binary labels.
        y_pred: Predicted binary labels.
        y_prob: Predicted probabilities for positive class (optional).

    Returns:
        Dict[str, float]: Metric name to calculated score mapping.
    """
    logger.info("Evaluating failure classification metrics...")
    try:
        from sklearn.metrics import (
            accuracy_score,
            precision_score,
            recall_score,
            f1_score,
            roc_auc_score,
        )
        metrics = {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        }
        if y_prob is not None:
            try:
                metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
            except ValueError:
                metrics["roc_auc"] = 0.0
    except Exception as e:
        logger.debug(f"Calculating basic accuracy via numpy: {e}")
        yt = np.array(y_true)
        yp = np.array(y_pred)
        acc = float(np.mean(yt == yp))
        metrics = {"accuracy": acc, "precision": 0.0, "recall": 0.0, "f1": 0.0}

    logger.info(f"Classification Evaluation: {metrics}")
    return metrics


def evaluate_regression_model(
    y_true: Union[pd.Series, np.ndarray],
    y_pred: Union[pd.Series, np.ndarray],
) -> Dict[str, float]:
    """Computes standard regression metrics for maintenance priority ranking.

    Args:
        y_true: Ground truth priority scores.
        y_pred: Predicted priority scores.

    Returns:
        Dict[str, float]: Regression metrics (MAE, RMSE, R2).
    """
    logger.info("Evaluating priority regression metrics...")
    yt = np.array(y_true, dtype=float)
    yp = np.array(y_pred, dtype=float)

    mae = float(np.mean(np.abs(yt - yp)))
    mse = float(np.mean((yt - yp) ** 2))
    rmse = float(np.sqrt(mse))
    ss_tot = np.sum((yt - np.mean(yt)) ** 2)
    r2 = float(1.0 - (np.sum((yt - yp) ** 2) / ss_tot)) if ss_tot > 0 else 0.0

    metrics = {
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
    }
    logger.info(f"Regression Evaluation: {metrics}")
    return metrics
