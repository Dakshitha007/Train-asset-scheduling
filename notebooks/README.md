# RailOpt AI - Notebooks Directory

This directory contains Jupyter notebooks for exploratory data analysis (EDA), hypothesis generation, feature experimentation, and prototyping.

## Notebook Naming Convention

Please follow an ordered numeric prefix to maintain workflow clarity:

- `01_data_loading_and_understanding.ipynb` - Data loading, schema inspection, dimension checking, missingness, and data quality validation.
- `02_exploratory_data_analysis.ipynb` - Statistical distributions, correlation heatmaps, boxplots, pairplots, and visual defect analysis.
- `03_data_preprocessing.ipynb` - Missing value treatment, validation, categorical label encoding, domain feature engineering, scaling, and train/val/test splits.
- `04_model_benchmarking.ipynb` - Baseline model exploration, hyperparameter tuning, cross-validation.
- `05_maintenance_block_scheduling.ipynb` - Constraint satisfaction and mathematical optimization for maintenance window scheduling.

## Best Practices
1. **Keep Notebooks Clean**: Restart kernel and run all cells sequentially before committing.
2. **Refactor Code into `src/`**: Once an exploration or utility logic stabilizes, refactor it into the appropriate module in `src/`.
3. **Use Relative Paths**: Always reference paths via `src.config` rather than hardcoded local machine paths.
