import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SQLITE_PATH = f"sqlite:///{BASE_DIR / 'dpdp_audit.db'}"

DATABASE_URL = getattr(settings, "database_url", os.getenv("DATABASE_URL", DEFAULT_SQLITE_PATH))
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine_args = {}
if DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}
else:
    engine_args.update({
        "pool_size": 20, 
        "max_overflow": 40, 
        "pool_pre_ping": True,
        "pool_recycle": 1800
    })

engine = create_engine(DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    import models
    Base.metadata.create_all(bind=engine)