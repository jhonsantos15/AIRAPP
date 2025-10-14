"""
Dependencias para inyección en rutas FastAPI.
"""
from typing import Generator

from sqlalchemy.orm import Session

from src.core.database import get_session


def get_db() -> Generator[Session, None, None]:
    """
    Provee sesión de base de datos para FastAPI.
    Se usa como dependencia en rutas FastAPI.
    
    Yields:
        Sesión de SQLAlchemy
    """
    session = get_session()
    try:
        yield session
    finally:
        session.close()
