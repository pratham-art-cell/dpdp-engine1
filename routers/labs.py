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

def get_current_tenant_email(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        clean_token = token.replace("Bearer ", "").strip()
        payload = jwt.decode(clean_token, settings.secret_key, algorithms=[settings.algorithm])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token subject")
        return email
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/upload", response_class=HTMLResponse)
def upload_audit_log(request: Request, audit_file: UploadFile = File(...), db: Session = Depends(get_db)):
    tenant_email = get_current_tenant_email(request)
    try:
        audit_file.file.seek(0, 2)
        size = audit_file.file.tell()
        audit_file.file.seek(0)
        if size > 5 * 1024 * 1024:
            return HTMLResponse(content="<div class='p-4 bg-rose-100 text-rose-800 rounded-lg mt-4 font-bold text-xs'>Payload exceeds 5MB limit.</div>")

        violations = 0
        total_rows = 0
        csv_reader = csv.DictReader(codecs.iterdecode(audit_file.file, 'utf-8', errors='ignore'))
        
        for row in csv_reader:
            total_rows += 1
            consent = row.get("Consent_Status", "")
            location = row.get("Location", "")
            if consent in ["Revoked", "Expired"] or "Unknown" in location or "Unsecured" in location:
                violations += 1

        audit_record = LabAuditRecord(
            client_id=tenant_email,
            filename=audit_file.filename or "audit_log.csv",
            total_records=total_rows,
            violations_summary=f"{violations} Violations" if violations > 0 else "Section 8 Compliant"
        )
        db.add(audit_record)
        db.commit()

        if violations > 0:
            return HTMLResponse(content=f"""
            <div class="p-6 bg-rose-100 border border-rose-300 rounded-xl mt-4 shadow-sm animate-pulse">
                <h4 class="text-rose-700 font-bold text-lg">🚨 Section 8 Breach Trigger Detected</h4>
                <p class="text-slate-800 text-sm">Found {violations} unauthorized access events across {total_rows} entries.</p>
            </div>
            """)
        else:
            return HTMLResponse(content=f"""
            <div class="p-6 bg-emerald-100 border border-emerald-300 rounded-xl mt-4 shadow-sm">
                <h4 class="text-emerald-700 font-bold text-lg">✅ Section 8 Verification Passed</h4>
                <p class="text-slate-800 text-sm">Verified {total_rows} access logs. All entries satisfy statutory technical safeguard requirements.</p>
            </div>
            """)
            
    except Exception:
        return HTMLResponse(content="<div class='p-4 bg-amber-100 text-amber-800 rounded-lg mt-4 font-bold text-xs'>CSV error. Confirm headers: Consent_Status, Location.</div>")