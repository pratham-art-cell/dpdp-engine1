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
            <a href="/api/leads/download-checklist" target="_blank" class="inline-block px-5 py-2.5 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold rounded-xl transition-all shadow-sm">
                ⬇ View & Print Statutory Checklist
            </a>
        </div>
        """,
        status_code=status.HTTP_200_OK
    )

@router.get("/download-checklist", response_class=HTMLResponse)
def download_statutory_checklist():
    return """
    <!DOCTYPE html>
    <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>DPDP Statutory Checklist 2026 | ConsentLayer</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 40px; max-width: 800px; margin: auto; color: #1e293b; line-height: 1.6; }
                h1 { font-size: 22px; color: #4338ca; }
                h2 { font-size: 16px; margin-top: 24px; color: #0f172a; }
                p, li { font-size: 13px; }
            </style>
        </head>
        <body>
            <h1>ConsentLayer | DPDP Section 8 Statutory Compliance Checklist</h1>
            <p>Retain this technical safeguard record for statutory DPBI audit verification.</p>
            <hr style="border: 1px solid #e2e8f0; margin: 16px 0;" />
            <h2>1. Section 5 Notice Infrastructure</h2>
            <p>[ &nbsp; ] Multilingual notice served across 22 Eighth Schedule languages before sample or data collection.</p>
            <p>[ &nbsp; ] Zero pre-checked boxes on digital check-in tablets.</p>
            <h2>2. Section 8 Technical Safeguards</h2>
            <p>[ &nbsp; ] Tokenized report download URLs replacing raw PDF transfers on personal devices.</p>
            <p>[ &nbsp; ] Immutable cryptographic access logging enabled for all staff interactions.</p>
        </body>
    </html>
    """