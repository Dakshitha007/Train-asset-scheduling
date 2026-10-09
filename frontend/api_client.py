"""Small HTTP client for the existing RailOpt AI FastAPI service."""

from __future__ import annotations

import os
from typing import Any

import requests


DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT_SECONDS = 12


class ApiError(Exception):
    """User-safe API request failure."""


class ApiClient:
    def __init__(self, base_url: str | None = None) -> None:
        configured_url = base_url or os.getenv(
            "RAILOPT_API_URL", DEFAULT_API_BASE_URL
        )
        self.base_url = configured_url.rstrip("/")

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", path, params=params)

    def post(self, path: str, payload: dict[str, Any]) -> Any:
        return self._request("POST", path, json=payload)

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = requests.request(
                method,
                f"{self.base_url}{path}",
                timeout=REQUEST_TIMEOUT_SECONDS,
                **kwargs,
            )
        except requests.Timeout as exc:
            raise ApiError(
                "The backend did not respond in time. Please try again."
            ) from exc
        except requests.ConnectionError as exc:
            raise ApiError(
                "The backend is unavailable. Check that the FastAPI service is running."
            ) from exc
        except requests.RequestException as exc:
            raise ApiError("The backend request could not be completed.") from exc

        try:
            body = response.json()
        except ValueError as exc:
            if not response.ok:
                raise ApiError(
                    f"The backend returned HTTP {response.status_code}."
                ) from exc
            raise ApiError("The backend returned an invalid response.") from exc

        if not response.ok:
            detail = (
                body.get("detail") or body.get("message")
                if isinstance(body, dict)
                else None
            )
            if isinstance(detail, dict):
                detail = detail.get("message")
            if isinstance(detail, list):
                messages = [
                    f"{'.'.join(str(part) for part in item.get('loc', ()) if part != 'body')}: "
                    f"{item.get('msg', 'Invalid input')}"
                    for item in detail
                    if isinstance(item, dict)
                ]
                detail = "; ".join(messages) if messages else None
            if detail == "Request validation failed." and isinstance(body, dict):
                errors = (body.get("data") or {}).get("errors", [])
                if isinstance(errors, list):
                    messages = [
                        f"{'.'.join(str(part) for part in item.get('loc', ()) if part != 'body')}: "
                        f"{item.get('msg', 'Invalid input')}"
                        for item in errors
                        if isinstance(item, dict)
                    ]
                    if messages:
                        detail = "; ".join(messages)
            message = str(detail).strip() if detail else ""
            if not message:
                message = f"Backend request failed (HTTP {response.status_code})."
            raise ApiError(message)

        if isinstance(body, dict) and body.get("success") is False:
            raise ApiError(str(body.get("message") or "The backend request failed."))
        if isinstance(body, dict) and "data" in body:
            return body["data"]
        return body
