import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings

# Pull URL from settings or environment, fallback to SQLite for pure local testing
DATABASE_URL = getattr(settings, "database_url", os.getenv("DATABASE_URL", "sqlite:///./dpdp_audit.db"))

# SQLAlchemy 1.4+ requires 'postgresql://' instead of 'postgres://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine_args = {}
if DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL connection pooling settings for production stability
    engine_args.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True 
    })

engine = create_engine(DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency to generate and close database sessions per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Creates tables if they do not exist."""
    import models  # Ensures models are registered before creation
    Base.metadata.create_all(bind=engine)