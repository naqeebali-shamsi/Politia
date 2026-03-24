from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import NullPool

from app.config import get_settings

Base = declarative_base()

_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {}
        kwargs = {"echo": settings.database_echo, "pool_pre_ping": True}

        if settings.database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        elif "pooler" in settings.database_url or "neon.tech" in settings.database_url:
            # Neon pooler handles connection pooling server-side; use NullPool
            kwargs["poolclass"] = NullPool
        else:
            kwargs["pool_size"] = settings.database_pool_size
            kwargs["max_overflow"] = settings.database_max_overflow

        _engine = create_engine(settings.database_url, connect_args=connect_args, **kwargs)
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
