"""Central configuration module for RailOpt AI.

Defines all project paths using pathlib.Path and sets standard constants.
Do not hardcode filesystem paths elsewhere in the codebase.
"""

from pathlib import Path

# Base Project Directories
# src/config/config.py -> parent is src/config -> parent is src -> parent is PROJECT_ROOT
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Data Directories & Paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

# Primary Data File Paths
RAW_DATA_FILENAME = "railway_synthetic_training_dataset_7000.xlsx"
RAW_DATA_PATH = RAW_DATA_DIR / RAW_DATA_FILENAME
PROCESSED_DATA_PATH = PROCESSED_DATA_DIR / "railway_processed_features.parquet"
EXTERNAL_DATA_PATH = EXTERNAL_DATA_DIR

# Outputs Directories & Paths
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
MODEL_OUTPUT_PATH = OUTPUTS_DIR / "models"
FIGURE_OUTPUT_PATH = OUTPUTS_DIR / "figures"
REPORT_OUTPUT_PATH = OUTPUTS_DIR / "reports"
EDA_OUTPUT_PATH = OUTPUTS_DIR / "eda"

# Notebooks Directory
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

# Backward Compatibility Aliases
PRIMARY_RAW_DATA_PATH = RAW_DATA_PATH
MODELS_DIR = MODEL_OUTPUT_PATH
FIGURES_DIR = FIGURE_OUTPUT_PATH
REPORTS_DIR = REPORT_OUTPUT_PATH
EDA_DIR = EDA_OUTPUT_PATH

# Model & Artifact Artifact Paths
FAILURE_PREDICTOR_MODEL_PATH = MODEL_OUTPUT_PATH / "failure_predictor.joblib"
PRIORITY_REGRESSOR_MODEL_PATH = MODEL_OUTPUT_PATH / "priority_regressor.joblib"
FEATURE_ENCODER_PATH = MODEL_OUTPUT_PATH / "feature_encoder.joblib"

# Pipeline & Modeling Settings
RANDOM_STATE = 42
TEST_SIZE = 0.2
CV_FOLDS = 5

# Railway Optimization Constraints
MAX_DAILY_BLOCK_HOURS = 6.0
DEFAULT_CREW_AVAILABILITY = 5
