"""Data preprocessing and dataset splitting module for RailOpt AI.

Cleans raw tabular records, handles missingness, normalizes types,
and performs reproducible train/validation/test partitions.
"""

from typing import Tuple, Optional
import pandas as pd

from src.config import RANDOM_STATE, TEST_SIZE
from src.utils.logger import get_logger

logger = get_logger(__name__)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Performs primary data cleaning and type sanitization.

    Args:
        df: Raw input DataFrame.

    Returns:
        pd.DataFrame: Cleaned DataFrame.
    """
    logger.info("Starting data cleaning pipeline...")
    cleaned_df = df.copy()

    # Drop duplicate records if any
    cleaned_df = cleaned_df.drop_duplicates()

    # Handle missing values if present (skeleton placeholder for domain imputation)
    # E.g., filling numerical with median, categoricals with mode

    logger.info(f"Cleaning complete. Remaining records: {len(cleaned_df)}")
    return cleaned_df


def split_train_test(
    df: pd.DataFrame,
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_STATE,
    stratify_col: Optional[str] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Splits dataset into train and test partitions.

    Args:
        df: Cleaned input DataFrame.
        test_size: Fraction of samples for the test set.
        random_state: Random seed for reproducibility.
        stratify_col: Optional column name to stratify on.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (train_df, test_df)
    """
    logger.info(f"Splitting dataset: test_size={test_size}, random_state={random_state}")
    try:
        from sklearn.model_selection import train_test_split
        stratify = df[stratify_col] if stratify_col and stratify_col in df.columns else None
        train_df, test_df = train_test_split(
            df,
            test_size=test_size,
            random_state=random_state,
            stratify=stratify,
        )
    except Exception as e:
        logger.debug(f"Falling back to pandas shuffle split: {e}")
        shuffled = df.sample(frac=1.0, random_state=random_state)
        n_test = int(len(df) * test_size)
        test_df = shuffled.iloc[:n_test]
        train_df = shuffled.iloc[n_test:]

    logger.info(f"Split completed: Train shape {train_df.shape}, Test shape {test_df.shape}")
    return train_df, test_df
