from contextlib import contextmanager
from typing import Generator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


def _database_url() -> str:
    """Get database URL from settings, with SQLite fallback."""
    if settings.database_url:
        # If DATABASE_URL is set, use it (Postgres/Supabase)
        # Note: For Postgres, ensure psycopg2-binary is installed:
        # pip install psycopg2-binary
        db_url = settings.database_url
        # If it's a postgres URL but psycopg2 isn't available, warn but continue
        # SQLAlchemy will raise a helpful error if the driver is missing
        return db_url
    # Default to SQLite
    return f"sqlite+pysqlite:///{settings.sqlite_path}"


NAMING_CONVENTIONS = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTIONS)


# Lazy engine creation to avoid import-time Postgres dependency issues
_engine = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        db_url = _database_url()
        # For Postgres URLs, ensure psycopg2 is available
        if db_url.startswith("postgresql") or db_url.startswith("postgres"):
            try:
                import psycopg2  # noqa: F401
            except ImportError:
                raise ImportError(
                    "Postgres database URL detected but psycopg2-binary is not installed. "
                    "Install it with: pip install psycopg2-binary"
                )
        _engine = create_engine(
            db_url,
            echo=False,
            future=True,
            pool_pre_ping=True,
        )
    return _engine


# Create engine on module load for SQLite (common case)
# For Postgres, it will be created lazily
try:
    db_url = _database_url()
    if not (db_url.startswith("postgresql") or db_url.startswith("postgres")):
        _engine = create_engine(
            db_url,
            echo=False,
            future=True,
            pool_pre_ping=True,
        )
except Exception:
    # If engine creation fails, it will be created lazily
    pass

engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
