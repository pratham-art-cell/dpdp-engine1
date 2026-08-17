import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Billing & Access (Directly tied to the paywall logic in index.html)[cite: 1]
    has_paid = Column(Boolean, default=False)
    access_valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class LabAuditRecord(Base):
    __tablename__ = "lab_audit_records"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, index=True, nullable=False)  # Scoped to authenticated tenant email
    filename = Column(String, nullable=False)
    total_records = Column(Integer, default=0)
    violations_summary = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)