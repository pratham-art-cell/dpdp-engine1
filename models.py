from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    # --- NEW BILLING FIELDS ---
    has_paid = Column(Boolean, default=False)
    access_valid_until = Column(DateTime, nullable=True)
class LabAuditRecord(Base):
    __tablename__ = "lab_audit_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    audit_data = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
