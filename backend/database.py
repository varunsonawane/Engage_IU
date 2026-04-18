import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    # "postgresql://varunsonawane:postgres@localhost:5432/engageiu",
    "postgresql://engageiu_user:23PpyoQ7vzbKucheA0q10w7oah6EGjgV@dpg-d7hh9djbc2fs73dhb4ng-a/engageiu"
)


if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs connect_args for thread safety; PostgreSQL does not
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist."""
    from models import Student, Event, Attendance, EndpointPerformance  # noqa: F401
    Base.metadata.create_all(bind=engine)
