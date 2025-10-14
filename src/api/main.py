"""
Aplicación FastAPI principal.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import db, init_engine_and_session
from .routes import measurements, devices, reports

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación."""
    # Startup
    logger.info("Iniciando API FastAPI...")
    init_engine_and_session()
    logger.info("Base de datos inicializada")
    
    yield
    
    # Shutdown
    logger.info("Cerrando API FastAPI...")
    # No necesitamos cerrar la sesión aquí porque SQLAlchemy lo maneja
    logger.info("API cerrada correctamente")


def create_api() -> FastAPI:
    """
    Factory para crear instancia de FastAPI.
    
    Returns:
        Instancia configurada de FastAPI
    """
    app = FastAPI(
        title="AireApp IoT API",
        description="API REST para monitoreo de calidad del aire con sensores IoT",
        version="2.0.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rutas
    app.include_router(measurements.router, prefix="/api/v1", tags=["measurements"])
    app.include_router(devices.router, prefix="/api/v1", tags=["devices"])
    app.include_router(reports.router, prefix="/api/v1", tags=["reports"])

    @app.get("/")
    def root():
        return {
            "message": "AireApp IoT API",
            "version": "2.0.0",
            "docs": "/docs",
            "health": "/api/v1/health",
        }

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok", "service": "aireapp-api"}

    return app
