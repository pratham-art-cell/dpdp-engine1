import hmac
import hashlib
import json
import datetime
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from sqlalchemy.orm import Session

# Import your database connection and models
from database import get_db
import models
from config import settings

router = APIRouter(prefix="/webhooks", tags=["Billing"])

@router.post("/dodo")
async def dodo_payment_handler(request: Request, x_signature: str | None = Header(None), db: Session = Depends(get_db)):
    
    # 1. Check if signature exists
    if not x_signature:
        raise HTTPException(status_code=401, detail="Missing signature header")
        
    # 2. Read the raw request body ONLY ONCE
    payload_body = await request.body()
    
    # 3. Generate expected signature and compare it securely
    expected_sig = hmac.new(
        settings.dodo_webhook_secret.encode('utf-8'), 
        payload_body, 
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, x_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
    # 4. Parse the JSON from the body we already read
    payload = json.loads(payload_body)
    
    # 5. Handle the payment success event
    if payload.get("event") == "payment.succeeded":
        
        # Extract the email safely
        customer_data = payload.get("data", {}).get("customer", {})
        customer_email = customer_data.get("email")
        
        if customer_email:
            print(f"💰 PAYMENT RECEIVED FROM: {customer_email}")
            
            # Find the user in the PostgreSQL database
            user = db.query(models.User).filter(models.User.email == customer_email).first()
            
            if user:
                # Upgrade their account (1-year pass)
                user.has_paid = True
                user.access_valid_until = datetime.datetime.utcnow() + datetime.timedelta(days=365)
                
                # Save changes to the database
                db.commit()
                print(f"✅ ACCOUNT UPGRADED FOR: {customer_email}")
            else:
                print(f"⚠️ Warning: Payment received, but no user found with email {customer_email}")
                
    return {"status": "success"}
