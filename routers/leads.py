from typing import Optional
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from database import get_db
import models

router = APIRouter(prefix="/api/leads", tags=["Lead Generation"])

class ColdEmailWebhookPayload(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    company_name: Optional[str] = None
    lead_status: Optional[str] = "interested"

@router.post("/webhook", status_code=status.HTTP_200_OK)
def cold_email_lead_webhook(payload: ColdEmailWebhookPayload, db: Session = Depends(get_db)):
    normalized_email = payload.email.strip().lower()
    existing_lead = db.query(models.LeadCapture).filter(models.LeadCapture.email == normalized_email).first()
    if existing_lead:
        return {"status": "lead_already_exists", "email": normalized_email}

    lead = models.LeadCapture(
        email=normalized_email,
        organization_name=payload.company_name or "Outbound Prospect",
        source_url="cold_email_campaign",
        lead_magnet_type="outbound_positive_reply"
    )
    db.add(lead)
    db.commit()
    return {"status": "lead_captured", "email": normalized_email}

@router.post("/capture", response_class=HTMLResponse)
def capture_lead(
    request: Request,
    email: str = Form(...),
    org_name: str = Form(None),
    source_url: str = Form("/"),
    db: Session = Depends(get_db)
):
    normalized_email = email.strip().lower()
    lead = models.LeadCapture(
        email=normalized_email,
        organization_name=org_name.strip() if org_name else None,
        source_url=source_url,
        lead_magnet_type="statutory_dpdp_checklist_2026"
    )
    db.add(lead)
    db.commit()

    return HTMLResponse(
        content="""
        <div class="p-4 bg-emerald-50 border border-emerald-300 rounded-2xl text-center">
            <div class="text-emerald-800 font-bold text-sm mb-1">✓ Checklist Ready!</div>
            <p class="text-xs text-emerald-700 mb-3">Your clinic compliance package is generated.</p>
            <a href="/api/leads/download-checklist" target="_blank" class="inline-block px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold rounded-xl transition-all shadow-sm">
                ⬇ View & Print PDF Checklist
            </a>
        </div>
        """,
        status_code=status.HTTP_200_OK
    )

@router.get("/download-checklist", response_class=HTMLResponse)
def download_statutory_checklist():
    return """
    <html>
        <head><title>DPDP Compliance Checklist 2026 | ConsentLayer</title></head>
        <body style="font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: auto; color: #1e293b; background: #fff;">
            <h2 style="color: #4f46e5; font-size: 24px; font-weight: 900;">ConsentLayer | DPDP 2026 Statutory Checklist</h2>
            <p style="color: #64748b; font-size: 14px;">Print this document to PDF (Ctrl+P) and retain for your clinic's compliance records.</p>
            <hr style="border: 1px solid #e2e8f0; margin: 20px 0;"/>
            <h3 style="color: #0f172a;">1. Section 5(1) Notice Mandate</h3>
            <p>[ &nbsp; ] Multilingual Notice presented before collecting patient phone numbers.</p>
            <p>[ &nbsp; ] Exact purpose specified: "Diagnostic testing only".</p>
            <p>[ &nbsp; ] Clear procedure on how patient can withdraw consent.</p>
            <h3 style="color: #0f172a; margin-top: 30px;">2. Section 8 Safeguards & Audit Trails</h3>
            <p>[ &nbsp; ] Immutable time-stamped log of staff access to records.</p>
            <p>[ &nbsp; ] WhatsApp dispatch links tokenized for security verification.</p>
            <p>[ &nbsp; ] Session timeout enforced after 15 minutes of LIMS inactivity.</p>
        </body>
    </html>
    """