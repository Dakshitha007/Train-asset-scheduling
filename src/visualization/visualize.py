"""Data visualization and reporting module for RailOpt AI.

Provides publication-ready plots for:
- Asset failure risk distribution across railway zones and stations
- Feature importances and SHAP summary plots
- Maintenance block Gantt schedules and resource allocation charts
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd

from src.config import FIGURES_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


def plot_asset_risk_distribution(
    df: pd.DataFrame,
    risk_col: str = "priority_score",
    output_path: Optional[Path] = None,
) -> None:
    """Plots the distribution of asset maintenance priority scores.

    Args:
        df: Input DataFrame containing asset records.
        risk_col: Column name representing priority/risk score.
        output_path: Optional file path to save figure.
    """
    logger.info("Generating asset risk distribution plot...")
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError:
        logger.warning("matplotlib or seaborn not installed. Skipping plot generation.")
        return

    plt.figure(figsize=(10, 5))
    sns.histplot(df[risk_col], kde=True, bins=30, color="#1f77b4")
    plt.title("RailOpt AI - Asset Maintenance Priority Score Distribution", fontsize=14)
    plt.xlabel("Priority Score")
    plt.ylabel("Asset Count")
    plt.grid(True, linestyle="--", alpha=0.6)

    save_dest = output_path or (FIGURES_DIR / "risk_score_distribution.png")
    plt.tight_layout()
    plt.savefig(save_dest, dpi=300)
    plt.close()
    logger.info(f"Saved distribution plot to {save_dest}")


def plot_feature_importance(
    feature_names: List[str],
    importances: List[float],
    top_n: int = 15,
    output_path: Optional[Path] = None,
) -> None:
    """Plots top predictive features influencing failure risk.

    Args:
        feature_names: List of feature names.
        importances: List of corresponding feature importance weights.
        top_n: Number of top features to display.
        output_path: Optional file path to save figure.
    """
    logger.info(f"Generating top {top_n} feature importance plot...")
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError:
        logger.warning("matplotlib or seaborn not installed. Skipping plot generation.")
        return

    feat_df = (
        pd.DataFrame({"Feature": feature_names, "Importance": importances})
        .sort_values(by="Importance", ascending=False)
        .head(top_n)
    )

    plt.figure(figsize=(10, 6))
    sns.barplot(data=feat_df, x="Importance", y="Feature", palette="Blues_r")
    plt.title(f"RailOpt AI - Top {top_n} Features Driving Maintenance Priority", fontsize=14)
    plt.xlabel("Relative Importance")
    plt.ylabel("Asset / Operational Feature")
    plt.grid(True, linestyle="--", alpha=0.6)

    save_dest = output_path or (FIGURES_DIR / "feature_importance.png")
    plt.tight_layout()
    plt.savefig(save_dest, dpi=300)
    plt.close()
    logger.info(f"Saved feature importance plot to {save_dest}")


def plot_maintenance_schedule_gantt(
    schedule: List[Dict[str, Any]],
    output_path: Optional[Path] = None,
) -> None:
    """Plots a Gantt chart representing scheduled track maintenance blocks.

    Args:
        schedule: List of scheduled block entries with start/end hours and asset IDs.
        output_path: Optional file path to save figure.
    """
    logger.info("Generating maintenance schedule timeline chart...")
    # SKELETON: Timeline visualization placeholder
    save_dest = output_path or (FIGURES_DIR / "maintenance_block_schedule.png")
    logger.info(f"Schedule plot destination: {save_dest}")
