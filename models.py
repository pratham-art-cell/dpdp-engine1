from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    mobile = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    has_paid = Column(Boolean, default=False, nullable=False)
    access_valid_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False)

class LeadCapture(Base):
    __tablename__ = "lead_captures"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    organization_name = Column(String(255), nullable=True)
    source_url = Column(String(500), nullable=True)
    lead_magnet_type = Column(String(100), default="statutory_dpdp_checklist_2026", nullable=False)
    captured_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False)

class LabAuditRecord(Base):
    __tablename__ = "lab_audits"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(255), index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    total_records = Column(Integer, default=0, nullable=False)
    violations_summary = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False)