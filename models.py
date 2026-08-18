import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    has_paid = Column(Boolean, default=False)
    access_valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Client Profile Details for Settings/Invoicing
    full_name = Column(String, nullable=True)
    mobile = Column(String, nullable=True)
    address = Column(String, nullable=True)

class LabAuditRecord(Base):
    __tablename__ = "lab_audit_records"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, index=True, nullable=False)
    filename = Column(String, nullable=False)
    total_records = Column(Integer, default=0)
    violations_summary = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)