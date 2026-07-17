from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.environments import DATABASE_URL

session_maker = sessionmaker(
    bind=create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=1800,
    ),
    autoflush=False,
)


def get_session():
    session = session_maker()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
