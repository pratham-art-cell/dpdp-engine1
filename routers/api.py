from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from database import get_db
from models import LabAuditRecord
from routers.labs import get_current_client_id

router = APIRouter(prefix="/api/v1/labs", tags=["JSON API"])

class AuditResponse(BaseModel):
    id: int
    client_id: str
    filename: str
    total_records: int
    violations_summary: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

@router.get("/", response_model=List[AuditResponse])
def get_client_audits_api(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    client_id: str = Depends(get_current_client_id), 
    db: Session = Depends(get_db)
):
    """
    Returns a paginated JSON list of audit records ordered newest-first 
    for the authenticated tenant.
    """
    audits = (
        db.query(LabAuditRecord)
        .filter(LabAuditRecord.client_id == client_id)
        .order_by(LabAuditRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return audits