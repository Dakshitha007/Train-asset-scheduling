# RailOpt AI Backend

Production-oriented FastAPI service for railway asset records, maintenance-priority inference, CP-SAT block scheduling, and dashboard aggregates. The API loads the already-trained model and preprocessing artifacts once during startup; it never trains or reloads the model per request.

## Requirements

- Python 3.10 or newer
- Model artifacts from the completed preprocessing/training stages:
  - `outputs/models/best_model.pkl`
  - `outputs/models/feature_columns.pkl`
  - `outputs/models/scaler.pkl`
  - Six `encoder_<feature>.joblib` files in `outputs/models/encoders/`
- Native runtime compatibility for the serialized estimator dependencies and OR-Tools

## Setup

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
```

Edit `backend/.env` for the deployment. The default database URL targets local PostgreSQL and contains no username or password; inject credentials through the environment or a deployment secret manager. SQLite is supported only as an explicit local/test override. Never commit secrets or production credentials.

The backend loads `backend/.env` and then the repository-root `.env` if present. Settings can also be supplied directly as process environment variables. Artifact paths are repository-root relative by default.

## PostgreSQL Database

Create the database and a least-privilege application role using your PostgreSQL administration process. Do not put real credentials in source control. Set `DATABASE_URL` in `backend/.env` or your secret manager, for example using the SQLAlchemy driver form `postgresql+psycopg://<user>:<password>@<host>:5432/railopt_ai`.

The production app verifies connectivity at startup but does not create PostgreSQL tables automatically. Apply the checked-in Alembic migration before starting the API:

```powershell
python -m alembic upgrade head
```

After changing ORM models, create and review a new migration before applying it:

```powershell
python -m alembic revision --autogenerate -m "describe schema change"
python -m alembic upgrade head
```

Seed the administrator and deterministic sample assets, prediction history, and requests after setting a strong secret (at least 12 characters):

Set `ADMIN_PASSWORD` as a protected process environment variable or through a secret manager; do not put the value in a checked-in file or shell history. The seed tool expects the value in the process environment. Then run:

```powershell
python -m backend.scripts.seed
```

The script refuses to seed without `ADMIN_PASSWORD`, hashes it with Argon2, and does not reset an existing administrator's password. Sample assets, predictions, and requests are inserted idempotently.

For local SQLite-only tests, set `DATABASE_URL=sqlite:///./railopt-test.db` and `AUTO_CREATE_SQLITE_SCHEMA=true`; this path may create tables automatically and is not the production migration workflow.

### Database Architecture

- `users`: unique email, password hash, and checked role set (`Admin`, `Planner`, `Engineer`, `Viewer`).
- `railway_assets`: current asset state and validated operational inputs.
- `predictions`: append-only model results, linked to an asset.
- `maintenance_requests`: work requests linked to assets.
- `optimized_schedule`: at most one disposition per maintenance request, optionally grouped by `optimization_runs`.
- `audit_logs`: append-only actions with a nullable user reference; deleting a user preserves logs and sets `user_id` to null.
- Asset deletion cascades to predictions and requests; request deletion cascades to its schedule. Schedule/request is one-to-one.

Indexes cover asset ID/station/zone, prediction timestamp, request priority, schedule start, and audit lookup. Check constraints enforce valid roles/statuses, score/probability bounds, and physical non-negative or positive ranges. Asset details are stored once; historical predictions and work requests reference the asset by key.

## Run the API

From the repository root:

```powershell
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

For local development with reload:

```powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

The legacy import remains available as `uvicorn app.api:app --port 8000`.

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

When model artifacts are missing or invalid, the service logs the failure and starts in degraded mode: health reports `503`, prediction/optimization return `503`, and database-backed asset/dashboard endpoints remain available.

## Response Contract

Successful responses use a stable envelope:

```json
{
  "success": true,
  "message": "Maintenance priority predicted.",
  "data": {}
}
```

Errors use the same keys with `success: false`; validation details are available under `data.errors`. Responses include an `X-Request-ID` header. JSON logs contain request method, path, status, duration, and request ID.

## API Overview

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Service greeting |
| `GET` | `/health` | Database/model readiness |
| `GET` | `/assets` | Paginated asset list; optional `asset_type` and `zone` filters |
| `POST` | `/assets` | Create an asset |
| `GET` | `/assets/{asset_id}` | Retrieve one asset |
| `PATCH` | `/assets/{asset_id}` | Update an asset with full merged-data validation |
| `DELETE` | `/assets/{asset_id}` | Delete an asset and related audit records |
| `POST` | `/prediction` | Predict priority for one asset and persist the audit record |
| `POST` | `/prediction/batch` | Predict a bounded batch of assets |
| `POST` | `/optimization` | Predict request priorities, solve a maintenance schedule with OR-Tools CP-SAT, and persist it |
| `GET` | `/dashboard/summary` | Dashboard KPI aggregates |
| `GET` | `/dashboard/charts` | Chart-ready asset, priority, schedule, and trend aggregates |

Prediction input uses the raw, unscaled feature values accepted by the Pydantic schema. The service reproduces the saved Stage 3 encodings, engineered features, scaler transform, and stored model feature order. For bool categorical flags it applies the Stage 3 `Yes`/`No` encoder mapping.

The optimizer uses track IDs when supplied and falls back to station as the conflict group. Operational time windows, thresholds, crew capacity, and weighted objective coefficients are explicitly configured in the service/constants and should be reviewed by railway operations before use. Scheduling is decision support, not dispatch authority.

## Folder Guide

- `app/api/routes/`: thin endpoint handlers; delegates to services
- `app/api/router.py`: route aggregation
- `app/core/`: environment configuration, JSON logging, constants, dependencies, and model registry
- `app/database/`: SQLAlchemy engine/session, ORM records, and Pydantic v2 schemas
- `app/services/`: asset CRUD, model inference, CP-SAT scheduling, and dashboard calculations
- `app/utils/`: Stage 3 preprocessing parity and model/data validation helpers
- `migrations/`: Alembic runtime and versioned PostgreSQL schema revisions
- `scripts/seed.py`: idempotent Admin, sample asset, prediction-history, and request seed
- `../alembic.ini`: Alembic entrypoint configuration; DSN is loaded from environment settings
- `requirements.txt`: isolated backend/runtime dependencies
- `.env.example`: safe local configuration template

PostgreSQL schema changes are managed through Alembic migrations. SQLite schema auto-creation exists only to support local tests. Use a managed database, secret manager, TLS, least-privilege roles, and authenticated network access in production.
