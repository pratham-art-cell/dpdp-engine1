import csv
import io
from fastapi import UploadFile, File
# ... keep your other imports below ...
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from database import get_session
from models import Lab
from fastapi import Query
router = APIRouter(prefix="/labs", tags=["Labs"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def list_labs(
    request: Request, 
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, le=100),
    session: Session = Depends(get_session)
):
    # The Fix: Replaced .all() with strict database pagination
    labs = session.exec(select(Lab).offset(skip).limit(limit)).all()
    
    return templates.TemplateResponse(
        request=request, 
        name="partials/lab_list.html", 
        context={"labs": labs}
    )
@router.post("/add", response_class=HTMLResponse)
def add_lab(
    request: Request,
    lab_name: str = Form(...),
    uses_paper_ledgers: bool = Form(False),
    has_digital_consent_logs: bool = Form(False),
    session: Session = Depends(get_session)
):
    compliance = "Compliant" if has_digital_consent_logs else "Section 8 Violation"
    
    new_lab = Lab(
        lab_name=lab_name,
        uses_paper_ledgers=uses_paper_ledgers,
        has_digital_consent_logs=has_digital_consent_logs,
        compliance_status=compliance
    )
    session.add(new_lab)
    session.commit()

    labs = session.exec(select(Lab))
    
    # THE FIX: Use request=, name=, and context=
    return templates.TemplateResponse(
        request=request, 
        name="partials/lab_list.html", 
        context={"labs": labs}

    )
from fastapi import HTTPException
import csv
import io

@router.post("/upload", response_class=HTMLResponse)
async def upload_clinic_logs(
    request: Request,
    audit_file: UploadFile = File(...)
):
    # DEFENSE 1: Ensure it is actually a CSV
    if not audit_file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only .csv files are permitted.")

    try:
        contents = await audit_file.read()
        decoded_content = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded_content))
        
        # DEFENSE 2: Verify required columns exist before processing
        required_columns = ['Consent_Obtained', 'Location']
        if not all(col in csv_reader.fieldnames for col in required_columns):
            raise HTTPException(status_code=422, detail="CSV missing required DPDP columns.")

        violations = []
        risk_flags = []
        total_records = 0
        
        for row in csv_reader:
            total_records += 1
            if row.get('Consent_Obtained') == 'No':
                violations.append(row)
            if row.get('Location') == 'Outside_Network':
                risk_flags.append(row)
                
        return templates.TemplateResponse(
            request=request,
            name="partials/audit_report.html", 
            context={
                "total_records": total_records,
                "violations": violations,
                "risk_flags": risk_flags,
                "filename": audit_file.filename
            }
        )
        
    except UnicodeDecodeError:
        # DEFENSE 3: Catch corrupted file encodings
        raise HTTPException(status_code=400, detail="File encoding error. Please upload a valid UTF-8 CSV.")
    except Exception as e:
        # DEFENSE 4: Catch-all for unexpected crashes
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")