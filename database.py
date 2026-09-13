"""
Database connection setup.

By default this uses SQLite so you can run the whole project with
ZERO extra setup (no need to install Postgres to get started).

When you're ready to use real PostgreSQL, just change DATABASE_URL
below to something like:
    postgresql://username:password@localhost:5432/support_agent

Everything else in the project stays exactly the same — that's the
whole point of using SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# --- Change this one line later to switch to Postgres ---
DATABASE_URL = "sqlite:///./support_agent.db"

# connect_args is only needed for SQLite, harmless to leave in
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Gives each request its own database session, then closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
