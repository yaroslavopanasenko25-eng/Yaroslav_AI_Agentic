"""FastAPI application entrypoint for GuardianEye defense analytics services."""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="GuardianEye API",
    version="1.0.0",
    description="Backend services for Ukraine air raid defense analytics.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api/v1", tags=["v1"])


@api_router.get("/health", response_model=Dict[str, Any])
def api_health_check() -> Dict[str, Any]:
    """Provide versioned health metadata for upstream checks."""
    try:
        return {"status": "ok", "service": "guardianeye-backend", "version": "1.0.0"}
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.exception("Versioned health check failed")
        raise HTTPException(status_code=500, detail="Health check failed") from exc


@app.get("/health", response_model=Dict[str, str], tags=["root"])
def health_check() -> Dict[str, str]:
    """Provide root-level heartbeat endpoint for container probes."""
    try:
        return {"status": "healthy"}
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.exception("Root health check failed")
        raise HTTPException(status_code=500, detail="Health check failed") from exc


app.include_router(api_router)
