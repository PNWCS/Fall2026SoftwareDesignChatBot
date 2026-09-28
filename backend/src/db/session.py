from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import settings

DATABASE_URL = settings.database_url
DB_CONNECT_TIMEOUT_SECONDS = 5
DB_POOL_TIMEOUT_SECONDS = 5
DB_STATEMENT_TIMEOUT_MS = 10_000

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "connect_timeout": DB_CONNECT_TIMEOUT_SECONDS,
        "options": f"-c statement_timeout={DB_STATEMENT_TIMEOUT_MS}",
    },
    pool_pre_ping=True,
    pool_timeout=DB_POOL_TIMEOUT_SECONDS,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()