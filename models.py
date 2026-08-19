from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    mobile = Column(String, nullable=True)
    address = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    has_paid = Column(Boolean, default=False)
    access_valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class LeadCapture(Base):
    __tablename__ = "lead_captures"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    organization_name = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    lead_magnet_type = Column(String, default="statutory_dpdp_checklist_2026")
    captured_at = Column(DateTime, default=datetime.utcnow)