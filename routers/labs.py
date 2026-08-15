import csv
import io
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, status, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/labs", tags=["Labs"])
templates = Jinja2Templates(directory="templates")

# --- AUTHENTICATION SETUP ---
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Hardcoded store mapping client API keys to their respective client IDs 
# (In Phase 3/4, you will load these dynamically from your PostgreSQL database)
VALID_CLIENT_KEYS = {
    "clinic_live_key_alpha123": "clinic_alpha_mumbai",
    "clinic_live_key_beta456": "clinic_beta_delhi",
    "dev_test_key_789": "local_test_clinic"
}

async def verify_client_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Validates the incoming API key from the request header 
    and returns the associated client_id.
    """
    if not api_key or api_key not in VALID_CLIENT_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing API Key."
        )
    return VALID_CLIENT_KEYS[api_key]


# --- PROTECTED ROUTE ---
@router.post("/upload", response_class=HTMLResponse)
async def upload_clinic_logs(
    request: Request,
    audit_file: UploadFile = File(...),
    client_id: str = Depends(verify_client_api_key)  # <-- Enforces auth on every request & extracts client_id
):
    # DEFENSE 1: Ensure it is actually a CSV (with iOS lowercase safety)
    if not audit_file.filename.lower().endswith('.csv'):
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
            # FILTER/ISOLATION: Bind every row or query check to the authenticated client_id
            row['client_id'] = client_id
            
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
                "filename": audit_file.filename,
                "client_id": client_id  # Display which clinic's data was processed
            }
        )
        
    except UnicodeDecodeError:
        # DEFENSE 3: Catch corrupted file encodings
        raise HTTPException(status_code=400, detail="File encoding error. Please upload a valid UTF-8 CSV.")
    except Exception as e:
        # DEFENSE 4: Catch-all for unexpected crashes
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")