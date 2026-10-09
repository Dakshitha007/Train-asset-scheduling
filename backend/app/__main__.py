"""Run the backend with ``python -m backend.app``."""

import os

import uvicorn

from backend.app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=settings.environment == "development",
    )
