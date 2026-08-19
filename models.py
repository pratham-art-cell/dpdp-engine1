import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)

class LeadCapture(Base):
    __tablename__ = "lead_captures"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    organization_name = Column(String(255), nullable=True)
    source_url = Column(String(500), nullable=True)
    lead_magnet_type = Column(String(100), default="statutory_dpdp_checklist_2026")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)