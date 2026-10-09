"""General helper and I/O utility functions for RailOpt AI.

Includes directory safety checks, serialization wrappers, and metric formatting.
"""

from pathlib import Path
from typing import Any, Union
import json
import joblib


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensures that a directory exists, creating parents if necessary.

    Args:
        path: Path to the directory.

    Returns:
        Path: Path object pointing to the verified directory.
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def save_artifact(obj: Any, file_path: Union[str, Path]) -> None:
    """Saves a Python object using joblib serialization.

    Args:
        obj: Object to serialize.
        file_path: Destination file path.
    """
    path_obj = Path(file_path)
    ensure_directory(path_obj.parent)
    joblib.dump(obj, path_obj)


def load_artifact(file_path: Union[str, Path]) -> Any:
    """Loads a serialized object from disk.

    Args:
        file_path: Path to the serialized file.

    Returns:
        Any: Deserialized object.
    """
    path_obj = Path(file_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Artifact not found at {path_obj}")
    return joblib.load(path_obj)


def save_json(data: dict, file_path: Union[str, Path]) -> None:
    """Saves a dictionary as a formatted JSON file.

    Args:
        data: Dictionary data.
        file_path: Destination path.
    """
    path_obj = Path(file_path)
    ensure_directory(path_obj.parent)
    with open(path_obj, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
