"""Environment-backed backend configuration."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / "backend" / ".env", override=False)
load_dotenv(PROJECT_ROOT / ".env", override=False)


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_origins(value: str | None) -> tuple[str, ...]:
    raw = value or "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173"
    return tuple(origin.strip() for origin in raw.split(",") if origin.strip())


def _path_setting(name: str, default: Path) -> Path:
    configured = Path(os.getenv(name, str(default))).expanduser()
    return configured if configured.is_absolute() else PROJECT_ROOT / configured


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "RailOpt AI API")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://localhost:5432/railopt_ai",
    )
    database_echo: bool = _as_bool(os.getenv("DATABASE_ECHO"), False)
    auto_create_sqlite_schema: bool = _as_bool(
        os.getenv("AUTO_CREATE_SQLITE_SCHEMA"), True
    )
    model_path: Path = _path_setting(
        "MODEL_PATH", PROJECT_ROOT / "outputs" / "models" / "best_model.pkl"
    )
    feature_columns_path: Path = _path_setting(
        "FEATURE_COLUMNS_PATH", PROJECT_ROOT / "outputs" / "models" / "feature_columns.pkl"
    )
    scaler_path: Path = _path_setting(
        "SCALER_PATH", PROJECT_ROOT / "outputs" / "models" / "scaler.pkl"
    )
    encoders_dir: Path = _path_setting(
        "ENCODERS_DIR", PROJECT_ROOT / "outputs" / "models" / "encoders"
    )
    allowed_origins: tuple[str, ...] = _as_origins(os.getenv("ALLOWED_ORIGINS"))
    max_batch_size: int = int(os.getenv("MAX_BATCH_SIZE", "500"))
    solver_time_limit_seconds: int = int(os.getenv("SOLVER_TIME_LIMIT_SECONDS", "30"))


settings = Settings()
