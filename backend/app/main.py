from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.v1.router import api_router


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Politia API",
        description="India Public Accountability Dashboard — transparent, source-backed scorecards for Indian MPs",
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept"],
    )

    app.include_router(api_router)

    @app.get("/health")
    def health():
        return {"status": "ok", "version": settings.app_version}

    @app.get("/health/data")
    def health_data():
        """Debug endpoint: check data file availability."""
        from pathlib import Path
        from app.application.services.analytics_service import (
            _BACKEND_ROOT, _GOLD_DIR, _GEOJSON_DIR,
        )
        gold_files = list(_GOLD_DIR.glob("*")) if _GOLD_DIR.exists() else []
        geojson_files = list(_GEOJSON_DIR.glob("*")) if _GEOJSON_DIR.exists() else []
        return {
            "backend_root": str(_BACKEND_ROOT),
            "gold_dir": str(_GOLD_DIR),
            "gold_exists": _GOLD_DIR.exists(),
            "gold_files": [f.name for f in gold_files],
            "geojson_dir": str(_GEOJSON_DIR),
            "geojson_exists": _GEOJSON_DIR.exists(),
            "geojson_files": [f.name for f in geojson_files],
            "cwd": str(Path.cwd()),
        }

    return app


app = create_app()
