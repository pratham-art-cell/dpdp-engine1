from fastapi import APIRouter, UploadFile, File, Request, Header, HTTPException
from fastapi.responses import HTMLResponse
import csv
import io

router = APIRouter(prefix="/labs", tags=["labs"])

# 🚀 THE FIX: Restored the missing dependency that api.py needs to boot
def get_current_client_id(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")
    return "authorized_client_node"

@router.post("/upload", response_class=HTMLResponse)
async def upload_audit_log(request: Request, audit_file: UploadFile = File(...)):
    try:
        # Read and decode the uploaded CSV file
        contents = await audit_file.read()
        decoded = contents.decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))
        
        violations = 0
        total_rows = 0
        
        # Analyze the data for DPDP Section 33 compliance
        for row in reader:
            total_rows += 1
            consent = row.get("Consent_Status", "")
            location = row.get("Location", "")
            
            if consent in ["Revoked", "Expired"] or "Unknown" in location or "Unsecured" in location:
                violations += 1

        # Generate the visual HTML response for the dashboard
        if violations > 0:
            return HTMLResponse(content=f"""
            <div class="p-6 bg-danger/10 border border-danger/30 rounded-xl mt-4 shadow-sm animate-pulse">
                <div class="flex items-center gap-3 mb-2">
                    <span class="text-2xl">🚨</span>
                    <h4 class="text-danger font-bold text-lg">DPDP Compliance Violation Detected</h4>
                </div>
                <p class="text-slate-300 text-sm">Scanned {total_rows} logs. Found <span class="font-bold text-white">{violations} unauthorized access events</span>. Immediate action required.</p>
            </div>
            """)
        else:
            return HTMLResponse(content=f"""
            <div class="p-6 bg-success/10 border border-success/30 rounded-xl mt-4 shadow-sm">
                <div class="flex items-center gap-3 mb-2">
                    <span class="text-2xl">✅</span>
                    <h4 class="text-success font-bold text-lg">Audit Passed Successfully</h4>
                </div>
                <p class="text-slate-300 text-sm">Scanned {total_rows} logs. All data access complies with Section 33. No unauthorized exposure.</p>
            </div>
            """)
            
    except Exception as e:
        return HTMLResponse(content="<div class='p-4 bg-warning/10 text-warning border border-warning/50 rounded-lg mt-4'>Error processing file. Please ensure it is a valid CSV format.</div>")