import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session

# 🚨 THE FIX: Force SQLModel to read your tables before building the DB
import models 

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dpdp_audit.db")

engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session