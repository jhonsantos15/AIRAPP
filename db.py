from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

db = SQLAlchemy()
SessionLocal = None


def init_engine_and_session():
    """
    Crea un engine secundario estable (pool_pre_ping) a partir de la URL ya
    configurada en Flask-SQLAlchemy. Esto NO borra datos ni recrea tablas.
    """
    global SessionLocal
    engine = create_engine(db.engine.url, pool_pre_ping=True)
    SessionLocal = scoped_session(sessionmaker(bind=engine))
