# db.py
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Flask-SQLAlchemy (para usar dentro de la app Flask)
db = SQLAlchemy()

# ---- Ruta absoluta y estable a ./instance/aireapp.db ----
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)
DB_PATH = os.path.join(INSTANCE_DIR, "aireapp.db")
DEFAULT_DB_URI = f"sqlite:///{DB_PATH}"

# Objetos globales para uso fuera de Flask (CLI/ingesta/scripts)
engine = None
SessionLocal = None


def get_db_uri() -> str:
    """Devuelve la URI de la BD. Usa DATABASE_URL si existe; si no, sqlite en instance/."""
    return os.environ.get("DATABASE_URL", DEFAULT_DB_URI)


def init_engine_and_session(db_uri: str | None = None):
    """
    Inicializa (una sola vez) un engine y un SessionLocal para uso fuera del contexto Flask.
    Devuelve (engine, SessionLocal).
    """
    global engine, SessionLocal
    uri = db_uri or get_db_uri()

    # Si ya están creados, reutiliza
    if engine is not None and SessionLocal is not None:
        return engine, SessionLocal

    engine = create_engine(uri, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return engine, SessionLocal


# Helpers opcionales
def get_engine():
    """Obtiene el engine inicializado (o lo crea)."""
    eng, _ = init_engine_and_session()
    return eng


def get_session():
    """Crea una sesión nueva (recuerda cerrarla)."""
    _, Sess = init_engine_and_session()
    return Sess()


# --- compatibilidad con scripts antiguos ---
def sqlalchemy_uri_from_env():
    return get_db_uri()
