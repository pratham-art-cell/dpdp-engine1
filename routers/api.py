from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Import your Phase 2 database and models
from database import get_db
from models import LabAuditRecord

# Import the exact same security dependency used in your HTMX UI
from routers.labs import verify_client_api_key

router = APIRouter(prefix="/api/v1/labs", tags=["JSON API"])

# 1. Define Phase 2 Pydantic schemas (replaces the old Lab/LabCreate)
class AuditResponse(BaseModel):
    id: int
    client_id: str
    filename: str
    total_records: int
    violations_summary: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# 2. Secure JSON Endpoint
@router.get("/", response_model=List[AuditResponse])
def get_client_audits_api(
    client_id: str = Depends(verify_client_api_key), 
    db: Session = Depends(get_db)
):
    """
    Returns a pure JSON list of audit records ONLY for the authenticated tenant.
    """
    audits = db.query(LabAuditRecord).filter(LabAuditRecord.client_id == client_id).all()
    return audits