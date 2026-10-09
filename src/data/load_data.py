"""Data loading and schema validation module for RailOpt AI.

Handles importing railway asset inspection and synthetic operational records
from raw Excel/CSV formats into structured pandas DataFrames.
"""

from pathlib import Path
from typing import Optional, List
import pandas as pd

from src.config.config import RAW_DATA_PATH
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Expected Schema Columns for Railway Asset Records
EXPECTED_COLUMNS: List[str] = [
    "asset_id",
    "asset_type",
    "zone",
    "station",
    "asset_age_years",
    "last_maintenance_days",
    "defect_count",
    "defect_severity",
    "inspection_score",
    "train_frequency",
    "average_speed",
    "weather",
    "temperature",
    "rainfall",
    "axle_load",
    "crew_available",
    "maintenance_duration",
    "passenger_peak",
    "nearby_alternate_track",
    "previous_failures",
    "predicted_failure_probability",
    "priority_score",
]


def load_raw_dataset(file_path: Optional[Path] = None) -> pd.DataFrame:
    """Loads raw railway asset inspection records from Excel or CSV file.

    Args:
        file_path: Optional path to the raw data file. Defaults to RAW_DATA_PATH.

    Returns:
        pd.DataFrame: Loaded dataset.

    Raises:
        FileNotFoundError: If the source data file does not exist.
    """
    target_path = file_path or RAW_DATA_PATH

    if not target_path.exists():
        logger.error(f"Raw data file not found: {target_path}")
        raise FileNotFoundError(f"Source file does not exist: {target_path}")

    logger.info(f"Loading raw dataset from {target_path}...")
    if target_path.suffix in [".xlsx", ".xls"]:
        df = pd.read_excel(target_path)
    elif target_path.suffix == ".csv":
        df = pd.read_csv(target_path)
    else:
        raise ValueError(f"Unsupported file format: {target_path.suffix}")

    logger.info(f"Successfully loaded {len(df)} records with {len(df.columns)} columns.")
    return df


def validate_dataset_schema(df: pd.DataFrame) -> bool:
    """Validates that loaded DataFrame conforms to required RailOpt AI schema.

    Args:
        df: Input DataFrame.

    Returns:
        bool: True if schema conforms to expected columns.
    """
    missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.warning(f"Schema validation warning: Missing columns {missing_cols}")
        return False
    logger.info("Schema validation passed successfully.")
    return True
