import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    # Billing & Access
    has_paid = Column(Boolean, default=False)
    access_valid_until = Column(DateTime, nullable=True)

class LabAuditRecord(Base):
    __tablename__ = "lab_audit_records"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, index=True)  # Scoped to authenticated tenant email
    filename = Column(String)
    total_records = Column(Integer)
    violations_summary = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)