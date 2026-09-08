from fastapi import APIRouter, UploadFile, File, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import csv
import codecs
import jwt
from database import get_db
from models import LabAuditRecord
from config import settings

router = APIRouter(prefix="/labs", tags=["labs"])

def get_current_tenant_email(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        clean_token = token.replace("Bearer ", "").strip()
        payload = jwt.decode(clean_token, settings.secret_key, algorithms=[settings.algorithm])
        return payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/upload", response_class=HTMLResponse)
def upload_audit_log(request: Request, audit_file: UploadFile = File(...), db: Session = Depends(get_db)):
    tenant_email = get_current_tenant_email(request)
    try:
        violations = 0
        total_rows = 0
        csv_reader = csv.DictReader(codecs.iterdecode(audit_file.file, 'utf-8'))
        
        for row in csv_reader:
            total_rows += 1
            consent = row.get("Consent_Status", "")
            location = row.get("Location", "")
            if consent in ["Revoked", "Expired"] or "Unknown" in location or "Unsecured" in location:
                violations += 1

        audit_record = LabAuditRecord(
            client_id=tenant_email,
            filename=audit_file.filename,
            total_records=total_rows,
            violations_summary=f"{violations} Violations" if violations > 0 else "Clean Pass"
        )
        db.add(audit_record)
        db.commit()

        if violations > 0:
            return HTMLResponse(content=f"""
            <div class="p-6 bg-rose-100 border border-rose-300 rounded-xl mt-4 shadow-sm animate-pulse">
                <h4 class="text-rose-700 font-bold text-lg">🚨 DPDP Violation Detected</h4>
                <p class="text-slate-800 text-sm">Found {violations} unauthorized access events in {total_rows} records.</p>
            </div>
            """)
        else:
            return HTMLResponse(content=f"""
            <div class="p-6 bg-emerald-100 border border-emerald-300 rounded-xl mt-4 shadow-sm">
                <h4 class="text-emerald-700 font-bold text-lg">✅ Audit Passed</h4>
                <p class="text-slate-800 text-sm">Scanned {total_rows} logs successfully.</p>
            </div>
            """)
            
    except Exception as e:
        return HTMLResponse(content="<div class='p-4 bg-amber-100 text-amber-800 rounded-lg mt-4'>Error processing CSV file. Please ensure it has Consent_Status and Location headers.</div>")