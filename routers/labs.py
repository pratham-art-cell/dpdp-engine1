import csv
import io
import json
import jwt
import codecs  # Required for high-performance file streaming
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db

# Import models securely
from models import LabAuditRecord, User

router = APIRouter(prefix="/labs", tags=["Labs"])
templates = Jinja2Templates(directory="templates")

# JWT Secret (Must match the one in auth.py)
SECRET_KEY = "your-super-secret-development-key"
ALGORITHM = "HS256"

async def get_current_client_id(request: Request) -> str:
    """
    Extracts and verifies the JWT token from the HTTP-only cookie, 
    returning the user's email as their unique tenant client_id.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Please log in to access audit tools."
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid authentication token.")
        return email
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please log in again."
        )


# --- ROUTE 1: GET LABS (Strictly Filtered by Authenticated Client) ---
@router.get("/", response_class=HTMLResponse)
async def list_client_labs(
    request: Request,
    client_id: str = Depends(get_current_client_id),
    db: Session = Depends(get_db)
):
    """
    Retrieves audit logs belonging ONLY to the authenticated tenant.
    Prevents Clinic A from ever seeing Clinic B's data.
    """
    client_labs = db.query(LabAuditRecord).filter(LabAuditRecord.client_id == client_id).all()
    
    return templates.TemplateResponse(
        name="partials/lab_list.html",
        context={
            "request": request,  # Fixed Template context signature
            "labs": client_labs,
            "client_id": client_id
        }
    )


# --- ROUTE 2: UPLOAD & PROCESS LOGS (Scoped & Memory Protected) ---
@router.post("/upload", response_class=HTMLResponse)
async def upload_clinic_logs(
    request: Request,
    audit_file: UploadFile = File(...),
    client_id: str = Depends(get_current_client_id),  # Enforces auth & injects client_id
    db: Session = Depends(get_db)
):
    # 🚨 CRITICAL FIX 1: The Paywall API Bypass
    # Check if the user exists and actually paid for the subscription.
    user = db.query(User).filter(User.email == client_id).first()
    if not user or not user.has_paid:
        raise HTTPException(status_code=403, detail="Active subscription required. Please upgrade your account.")

    # DEFENSE 1: Ensure it is a CSV
    if not audit_file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only .csv files are permitted.")

    try:
        # 🚀 CRITICAL FIX 2: High-Performance RAM Streaming (Prevents server crashes)
        # Instead of reading the whole file to memory, we stream it directly line-by-line
        csv_reader = csv.DictReader(codecs.iterdecode(audit_file.file, 'utf-8'))
        
        required_columns = ['Consent_Obtained', 'Location']
        violations = []
        risk_flags = []
        total_records = 0
        
        for row in csv_reader:
            # DEFENSE 2: Validate columns on the very first row
            if total_records == 0:
                if not all(col in csv_reader.fieldnames for col in required_columns):
                    raise HTTPException(status_code=422, detail="CSV missing required DPDP Section 33 columns.")

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
                
        # 🔧 CRITICAL FIX 3: TemplateResponse Signature
        return templates.TemplateResponse(
            name="partials/audit_report.html", 
            context={
                "request": request, 
                "total_records": total_records,
                "violations": violations,
                "risk_flags": risk_flags,
                "filename": audit_file.filename,
                "client_id": client_id
            }
        )
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding error. Please upload a valid UTF-8 CSV.")
    except HTTPException:
        # Pass HTTPExceptions straight through to the frontend
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Audit processing failed: {str(e)}")
    finally:
        # Ensure the file stream is closed to prevent OS memory leaks
        audit_file.file.close()