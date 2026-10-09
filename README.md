# 🚆 RailOpt AI: AI-Powered Railway Maintenance Optimization System

[![Smart India Hackathon](https://img.shields.io/badge/Smart%20India%20Hackathon-SIH%202024%2F2025-orange.svg)](https://sih.gov.in/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Architecture](https://img.shields.io/badge/Architecture-Clean%20DS%20Standards-brightgreen.svg)](#project-structure)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent decision-support system designed for **Indian Railways** to predict track asset degradation, rank maintenance urgency, and mathematically optimize **Maintenance Block Windows** to minimize train traffic disruption and passenger delays.

---

## 📌 Problem Overview & Objectives

In railway operations, a **"Block"** represents a temporary suspension of train traffic over a designated track section to enable engineering crews and heavy track-tamping machinery to carry out essential maintenance. 

Scheduling these blocks manually presents major challenges:
1. **Safety vs. Throughput**: Balancing asset failure risks against tight passenger and freight timetables.
2. **Resource Constraints**: Coordinating specialized maintenance gangs, track machines, and materials across geographically dispersed zones.
3. **Traffic Disruption**: Preventing bottleneck cascades and massive train delays on critical corridors.

**RailOpt AI** addresses this through a modular, two-tier AI architecture:
- **Tier 1 (Predictive ML)**: Predicts asset failure probability and estimates a composite priority score using track geometry, defect severity, traffic tonnage (axle loads), and climate conditions.
- **Tier 2 (Prescriptive Optimization)**: Schedules optimal maintenance block windows using mathematical optimization (MILP / constraint satisfaction) while respecting crew availability and traffic constraints.

---

## 🏗️ Project Structure

The project adheres to industry-standard data science clean architecture (inspired by Cookiecutter Data Science and production MLOps standards):

```
RailOptAI/
│
├── data/                            # Project data repository (separated by mutation stage)
│   ├── raw/                         # Immutable original data (Excel, CSV, sensor records)
│   │   └── railway_synthetic_training_dataset_7000.xlsx
│   ├── processed/                   # Cleaned, normalized, and feature-engineered datasets
│   └── external/                    # Third-party inputs (GIS data, timetable feeds, weather data)
│
├── notebooks/                       # Ordered Jupyter notebooks for research & exploration
│   ├── 01_data_loading_and_understanding.ipynb  # Stage 1: Ingestion, schema audit, sanity checks
│   └── README.md
│
├── src/                             # Core reusable production source code
│   ├── __init__.py
│   ├── config/                      # Centralized configuration management
│   │   ├── __init__.py
│   │   └── config.py                # Global filesystem paths (pathlib) and constants
│   ├── data/                        # Ingestion, validation, and preprocessing
│   │   ├── __init__.py
│   │   ├── load_data.py             # Excel/CSV loading & schema validation
│   │   └── preprocess.py            # Type coercion, cleaning & train-test split
│   ├── features/                    # Feature engineering & transformation pipelines
│   │   ├── __init__.py
│   │   └── build_features.py        # Track stress indices & ColumnTransformers
│   ├── models/                      # ML modeling & optimization packages
│   │   ├── __init__.py
│   │   ├── train.py                 # Priority-regressor training, validation selection & artifact export
│   │   ├── predict.py               # Batch and single-sample scoring templates
│   │   ├── evaluate.py              # Classification & regression metric computation
│   │   └── optimize.py              # Maintenance block window scheduling solver
│   ├── visualization/               # Diagnostic and reporting charts
│   │   ├── __init__.py
│   │   └── visualize.py             # Risk distributions, feature importance & Gantt plots
│   └── utils/                       # Shared utility functions
│       ├── __init__.py
│       ├── logger.py                # Structured console & file logging
│       └── helpers.py               # Safe I/O, artifact persistence & directory utilities
│
├── outputs/                         # Generated artifacts (ignored by git except .gitkeep)
│   ├── eda/                         # Exploratory data analysis visual outputs
│   │   # Stores: Correlation Heatmaps, Distribution Plots, Boxplots, Pairplots, Feature Importance Charts
│   ├── figures/                     # Production plots, ROC curves, and Gantt charts
│   ├── models/                      # Serialized model weights & encoders (.joblib / .pkl)
│   └── reports/                     # Evaluation summaries, CSV audits, and validation metrics
│
├── app/                             # Backend REST API service (FastAPI)
│   ├── __init__.py
│   ├── api.py                       # REST API endpoints for inference and scheduling
│   └── schemas.py                   # Pydantic data validation schemas
│
├── frontend/                        # Interactive operations dashboard (Streamlit)
│   ├── app.py                       # UI for section engineers and block controllers
│   └── README.md
│
├── requirements.txt                 # Exact dependencies for data science, optimization & web apps
├── pyproject.toml                   # Project packaging and metadata configuration
├── README.md                        # Project documentation
├── .gitignore                       # Comprehensive Git exclusion rules
└── main.py                          # CLI pipeline runner and workflow orchestrator
```

---

## 📂 Detailed Folder Responsibilities

| Directory | Purpose & Contents |
| :--- | :--- |
| `data/raw/` | Stores immutable original source data (`railway_synthetic_training_dataset_7000.xlsx`). Never modified by code. |
| `data/processed/` | Stores cleaned, encoded, and transformed datasets ready for model consumption. |
| `data/external/` | Stores supplementary third-party data (e.g., weather feeds, section gradient tables, timetable data). |
| `notebooks/` | Numbered step-by-step Jupyter notebooks for experimentation (e.g., `01_data_loading_and_understanding.ipynb`). |
| `src/config/` | Contains `config.py`, defining all paths via `pathlib.Path` (`PROJECT_ROOT`, `RAW_DATA_PATH`, `MODEL_OUTPUT_PATH`, etc.) and system seeds. |
| `src/data/` | Ingestion scripts (`load_data.py`) and data cleaning / splitting utilities (`preprocess.py`). |
| `src/features/` | Feature extraction logic (e.g., track stress burden, defect pressure rate) and scikit-learn transformers. |
| `src/models/` | Priority-regressor training (`train.py`), evaluation metrics (`evaluate.py`), and separate inference/optimization modules that remain incomplete. |
| `src/visualization/`| Publication-ready plotting functions for distributions, feature importance, and block timeline Gantt charts. |
| `src/utils/` | Centralized logging (`logger.py`) and helper routines (`helpers.py`) for directory safety and artifact serialization. |
| `outputs/eda/` | Stores exploratory visual artifacts: **Correlation Heatmaps**, **Distribution Plots**, **Boxplots**, **Pairplots**, and **Feature Importance Charts**. |
| `outputs/figures/` | Stores generated diagnostic plots, model comparison charts, and schedule timeline graphics. |
| `outputs/models/` | Stores trained model binaries (`.joblib`, `.pkl`), feature scalers, and encoders. |
| `outputs/reports/` | Stores generated CSV audit reports, evaluation metrics, and performance tables. |
| `app/` | Production-ready FastAPI application providing REST endpoints (`/predict`, `/optimize-blocks`, `/health`). |
| `frontend/` | Interactive Streamlit operations dashboard for railway controllers and permanent way inspectors. |

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10 or higher
- Git

### 2. Environment Setup

Clone or open the repository, then create and activate a virtual environment:

```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

Install all project dependencies specified in `requirements.txt`:

```bash
pip install -r requirements.txt
```

To enable editable imports across notebooks and scripts without path manipulation:

```bash
pip install -e .
```

---

## 💻 Usage & CLI Workflows

The `main.py` entrypoint allows running individual or multi-stage pipelines:

### Check Project Environment & Status
```bash
python main.py --stage status
```

### Run Data Ingestion & Validation
```bash
python main.py --stage data
```

### Execute with a Custom Dataset
```bash
python main.py --stage data --file path/to/custom_dataset.xlsx
```

### Train the Maintenance Priority Model
Run after the preprocessing stage has created `data/processed/train.csv`,
`validation.csv`, and `test.csv`, as well as the fitted scaler and encoders in
`outputs/models/`:

```bash
python main.py --stage train
```

The training stage compares a gradient-boosted tree regressor with a
regularized linear booster using validation R² (validation RMSE breaks ties),
refits the selected model on the train and validation splits, and reports
held-out test metrics. It saves `best_model.pkl`, `feature_columns.pkl`, and
`outputs/reports/training_metrics.json`; it validates and reuses the
preprocessing artifacts generated by Stage 3.

---

## 📓 Running the Initial Notebook

Open the Stage 1 Jupyter notebook to validate and understand the dataset:

```bash
jupyter notebook notebooks/01_data_loading_and_understanding.ipynb
```

The notebook performs 12 systematic stages of data inspection:
1. Project Introduction
2. Library Imports & Runtime Environment Check
3. Pathlib-based Raw Dataset Loading
4. Dataset Previews (`head()`, `tail()`, random 10 rows)
5. Dimension Auditing (Row & Column counts)
6. Column Information (Data types, Non-null counts, In-memory footprint)
7. Missing Value Audit Table
8. Duplicate Record Analysis
9. Railway Domain Data Quality & Physical Bounds Checks
10. Statistical Summaries (Parametric and Categorical `describe()`)
11. Feature Taxonomy Separation (Numerical, Categorical, Target, Identifier)
12. Executive Dataset Health Audit Report & Pre-EDA Recommendations

---

## 🌐 Running Backend & Frontend Services

### Start FastAPI REST Server
```bash
uvicorn app.api:app --reload --port 8000
```
Interactive Swagger documentation is available at: `http://127.0.0.1:8000/docs`

### Launch Streamlit Dashboard
```bash
streamlit run frontend/app.py
```
Dashboard will open at: `http://localhost:8501`

---

## 📊 Dataset Schema Overview

The raw dataset (`data/raw/railway_synthetic_training_dataset_7000.xlsx`) contains 7,000 synthetic railway asset inspection records with the following key attributes:

| Feature Category | Columns |
| :--- | :--- |
| **Asset Identity** | `asset_id`, `asset_type`, `zone`, `station`, `asset_age_years` |
| **Track Condition** | `last_maintenance_days`, `defect_count`, `defect_severity`, `inspection_score`, `previous_failures` |
| **Traffic & Operations** | `train_frequency`, `average_speed`, `axle_load`, `passenger_peak`, `nearby_alternate_track` |
| **Environment** | `weather`, `temperature`, `rainfall` |
| **Maintenance Resources**| `crew_available`, `maintenance_duration` |
| **Target Variables** | `predicted_failure_probability`, `priority_score` |

---

## 🗺️ Machine Learning & Optimization Roadmap

- [x] Phase 1: Clean Architecture Project Structure & Module Organization
- [x] Stage 1 Notebook: Data Loading, Quality Validation & Schema Understanding (`01_data_loading_and_understanding.ipynb`)
- [x] Stage 2 Notebook: Exploratory Data Analysis & Defect Pattern Mining (`02_exploratory_data_analysis.ipynb`)
- [x] Stage 3 Notebook: Data Preprocessing & Domain Feature Engineering (`03_data_preprocessing.ipynb`)
- [ ] Phase 4: Failure Prediction & Priority Regressor Modeling (XGBoost / LightGBM)
- [ ] Phase 5: Mathematical Maintenance Block Scheduling Solver (MILP / OR-Tools / PuLP)
- [ ] Phase 6: API Integration & Full Interactive Dashboard Deployment
