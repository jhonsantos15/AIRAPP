"""
Database configuration and session management.
"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from flask_sqlalchemy import SQLAlchemy
from contextlib import contextmanager

# Flask-SQLAlchemy instance
db = SQLAlchemy()

# Global engine and session for non-Flask contexts (CLI, scripts)
engine = None
SessionLocal = None


def get_db_uri() -> str:
    """
    Returns the database URI.
    Uses DATABASE_URL environment variable or defaults to SQLite in instance/.
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    instance_dir = base_dir / "instance"
    instance_dir.mkdir(exist_ok=True)
    
    default_uri = f"sqlite:///{instance_dir / 'aireapp.db'}"
    return os.environ.get("DATABASE_URL", default_uri)


def init_engine_and_session(db_uri: str | None = None) -> tuple:
    """
    Initializes (once) an engine and SessionLocal for use outside Flask context.
    Returns (engine, SessionLocal).
    """
    global engine, SessionLocal
    
    if engine is not None and SessionLocal is not None:
        return engine, SessionLocal
    
    uri = db_uri or get_db_uri()
    engine = create_engine(
        uri,
        future=True,
        pool_pre_ping=True,  # Verifica conexiones antes de usarlas
        echo=False  # Cambiar a True para debug de SQL
    )
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True
    )
    
    return engine, SessionLocal


def get_engine():
    """Gets the initialized engine (or creates it)."""
    eng, _ = init_engine_and_session()
    return eng


def get_session() -> Session:
    """Creates a new session (remember to close it)."""
    _, sess_local = init_engine_and_session()
    return sess_local()


@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    Automatically commits and closes session.
    
    Usage:
        with get_db_session() as session:
            session.add(obj)
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Legacy compatibility
def sqlalchemy_uri_from_env():
    """Legacy function for backward compatibility."""
    return get_db_uri()
