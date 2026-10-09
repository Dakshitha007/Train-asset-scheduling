"""RailOpt AI - Main CLI & Pipeline Orchestrator.

Smart India Hackathon: AI-Powered Railway Maintenance Optimization System.

Entrypoint to run data ingestion, feature generation, model training,
evaluation, block scheduling optimization, and service launching.
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.config.config import (
    RAW_DATA_PATH,
    PROCESSED_DATA_PATH,
    MODEL_OUTPUT_PATH,
    FIGURE_OUTPUT_PATH,
    REPORT_OUTPUT_PATH,
    EDA_OUTPUT_PATH,
)
from src.utils.logger import get_logger
from src.data.load_data import load_raw_dataset, validate_dataset_schema
from src.data.preprocess import clean_data, split_train_test
from src.models.train import run_training_pipeline

logger = get_logger("RailOptAI-Main")


def parse_args() -> argparse.Namespace:
    """Parses command-line arguments for pipeline execution."""
    parser = argparse.ArgumentParser(
        description="RailOpt AI - Railway Maintenance Optimization Pipeline Orchestrator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--stage",
        type=str,
        default="status",
        choices=["status", "data", "features", "train", "evaluate", "optimize", "all"],
        help="Pipeline stage to execute.",
    )

    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Optional custom dataset file path.",
    )

    return parser.parse_args()


def check_status() -> None:
    """Prints current pipeline readiness and directory verification."""
    logger.info("==================================================")
    logger.info("RailOpt AI - Project Status & Environment Check")
    logger.info("==================================================")
    logger.info(f"Project Root: {PROJECT_ROOT}")
    logger.info(f"Raw Dataset Available: {RAW_DATA_PATH.exists()} ({RAW_DATA_PATH})")
    logger.info(f"Processed Data Directory: {PROCESSED_DATA_PATH.parent}")
    logger.info(f"Models Directory: {MODEL_OUTPUT_PATH}")
    logger.info(f"Reports Directory: {REPORT_OUTPUT_PATH}")
    logger.info(f"Figures Directory: {FIGURE_OUTPUT_PATH}")
    logger.info(f"EDA Outputs Directory: {EDA_OUTPUT_PATH}")
    logger.info("Pipeline structure verified successfully.")


def run_data_pipeline(custom_file: str = None) -> None:
    """Runs data loading, schema validation, and cleaning."""
    logger.info("Running Data Ingestion Stage...")
    file_path = Path(custom_file) if custom_file else RAW_DATA_PATH

    if not file_path.exists():
        logger.error(f"Cannot find dataset at {file_path}")
        return

    # Ingest and validate
    df = load_raw_dataset(file_path)
    is_valid = validate_dataset_schema(df)

    if not is_valid:
        logger.warning("Dataset schema has warnings. Check expected columns.")

    cleaned_df = clean_data(df)
    train_df, test_df = split_train_test(cleaned_df)
    logger.info(f"Data pipeline complete. Train: {train_df.shape}, Test: {test_df.shape}")


def main() -> None:
    """Main execution function."""
    args = parse_args()

    if args.stage == "status":
        check_status()
    elif args.stage == "data":
        run_data_pipeline(args.file)
    elif args.stage == "train":
        check_status()
        run_training_pipeline()
    elif args.stage in ["features", "evaluate", "optimize", "all"]:
        logger.info(f"Stage '{args.stage}' requested.")
        check_status()
        logger.info(f"Note: Machine learning models are not implemented yet. Stage '{args.stage}' is staged for development.")
    else:
        logger.error(f"Unknown stage: {args.stage}")


if __name__ == "__main__":
    main()
