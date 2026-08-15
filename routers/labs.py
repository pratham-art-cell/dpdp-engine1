import csv
import io
import json
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, status, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import LabAuditRecord
router = APIRouter(prefix="/labs", tags=["Labs"])
templates = Jinja2Templates(directory="templates")

# --- AUTHENTICATION SETUP ---
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Hardcoded per-client API keys (Transitioning to PostgreSQL table storage in Phase 3)
VALID_CLIENT_KEYS = {
    "clinic_mumbai_live_key_99": "clinic_mumbai_01",
    "clinic_delhi_live_key_88": "clinic_delhi_02",
    "dev_test_key_789": "local_test_clinic"
}

async def verify_client_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Enforces authentication on every route and returns the isolated client_id.
    """
    if not api_key or api_key not in VALID_CLIENT_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing API Key. Access denied."
        )
    return VALID_CLIENT_KEYS[api_key]


# --- ROUTE 1: GET LABS (Strictly Filtered by Authenticated Client) ---
@router.get("/", response_class=HTMLResponse)
async def list_client_labs(
    request: Request,
    client_id: str = Depends(verify_client_api_key),
    db: Session = Depends(get_db)
):
    """
    Retrieves audit logs belonging ONLY to the authenticated tenant.
    Prevents Clinic A from ever seeing Clinic B's data.
    """
    # CRITICAL FIX: Filter query strictly by authenticated client_id
    client_labs = db.query(LabAuditRecord).filter(LabAuditRecord.client_id == client_id).all()
    
    return templates.TemplateResponse(
        request=request,
        name="partials/lab_list.html",
        context={
            "labs": client_labs,
            "client_id": client_id
        }
    )


# --- ROUTE 2: UPLOAD & PROCESS LOGS (Scoped to Client) ---
@router.post("/upload", response_class=HTMLResponse)
async def upload_clinic_logs(
    request: Request,
    audit_file: UploadFile = File(...),
    client_id: str = Depends(verify_client_api_key),  # Enforces auth & injects client_id
    db: Session = Depends(get_db)
):
    # DEFENSE 1: Ensure it is a CSV (with lowercase safety for iOS)
    if not audit_file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only .csv files are permitted.")

    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB guard against memory exhaustion
    contents = await audit_file.read()
    
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum upload size is 5MB.")

    try:
        decoded_content = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded_content))
        
        # DEFENSE 2: Verify required columns exist
        required_columns = ['Consent_Obtained', 'Location']
        if not all(col in csv_reader.fieldnames for col in required_columns):
            raise HTTPException(status_code=422, detail="CSV missing required DPDP Section 33 columns.")

        violations = []
        risk_flags = []
        total_records = 0
        
        for row in csv_reader:
            total_records += 1
            if row.get('Consent_Obtained') == 'No':
                violations.append(row)
            if row.get('Location') == 'Outside_Network':
                risk_flags.append(row)
                
        # Persist to database securely tagged with the authenticated client_id
        db_record = LabAuditRecord(
            client_id=client_id,
            filename=audit_file.filename,
            total_records=total_records,
            violations_summary=json.dumps({"violations": len(violations), "risks": len(risk_flags)})
        )
        db.add(db_record)
        db.commit()
                
        return templates.TemplateResponse(
            request=request,
            name="partials/audit_report.html", 
            context={
                "total_records": total_records,
                "violations": violations,
                "risk_flags": risk_flags,
                "filename": audit_file.filename,
                "client_id": client_id
            }
        )
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding error. Please upload a valid UTF-8 CSV.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Audit processing failed: {str(e)}")