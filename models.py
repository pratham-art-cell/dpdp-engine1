from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from config import settings

class LabAuditRecord(Base):
    __tablename__ = "lab_audit_records"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, index=True, nullable=False)  # <-- Tenant isolation key
    filename = Column(String, nullable=False)
    total_records = Column(Integer, default=0)
    violations_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())