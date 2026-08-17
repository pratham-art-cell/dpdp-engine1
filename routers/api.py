from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import LabAuditRecord

# Import the JWT cookie dependency from labs
from routers.labs import get_current_client_id

router = APIRouter(prefix="/api/v1/labs", tags=["JSON API"])

class AuditResponse(BaseModel):
    id: int
    client_id: str
    filename: str
    total_records: int
    violations_summary: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[AuditResponse])
def get_client_audits_api(
    client_id: str = Depends(get_current_client_id), 
    db: Session = Depends(get_db)
):
    """
    Returns a pure JSON list of audit records ONLY for the authenticated tenant.
    """
    audits = db.query(LabAuditRecord).filter(LabAuditRecord.client_id == client_id).all()
    return audits