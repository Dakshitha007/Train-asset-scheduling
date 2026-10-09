"""Backward-compatible import for the production backend application.

Use ``backend.app.main:app`` for new deployments.
"""

from backend.app.main import app

__all__ = ["app"]
