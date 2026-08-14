from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models import Lab, LabCreate

router = APIRouter(prefix="/api/v1/labs", tags=["JSON API"])

@router.post("/", response_model=Lab)
def create_lab_api(lab_data: LabCreate, session: Session = Depends(get_session)):
    # 1. Pydantic automatically validates lab_data against ConfigDict(extra="forbid")
    compliance = "Compliant" if lab_data.has_digital_consent_logs else "Section 8 Violation"
    
    # 2. Map Pydantic schema to SQLModel database object
    new_lab = Lab(
        lab_name=lab_data.lab_name,
        uses_paper_ledgers=lab_data.uses_paper_ledgers,
        has_digital_consent_logs=lab_data.has_digital_consent_logs,
        compliance_status=compliance
    )
    
    session.add(new_lab)
    session.commit()
    session.refresh(new_lab) # Fetches the new DB ID
    
    return new_lab # Returns pure JSON, not HTML