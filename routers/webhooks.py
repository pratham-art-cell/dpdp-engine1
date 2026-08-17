from fastapi import APIRouter, Request, HTTPException, Header, Depends
from sqlalchemy.orm import Session
import datetime

# Import your database connection and models
from database import get_db
import models
from config import settings

router = APIRouter(prefix="/webhooks", tags=["Billing"])

@router.post("/dodo")
async def dodo_payment_handler(request: Request, x_signature: str | None = Header(None), db: Session = Depends(get_db)):
    # 1. Security Check: Ensure the request actually came from Dodo Payments
    if not x_signature:
        raise HTTPException(status_code=401, detail="Missing signature header")
        
    # (Optional) You would typically verify the x_signature against settings.DODO_WEBHOOK_SECRET here
        
    # 2. Parse the webhook payload
    payload = await request.json()
    
    # 3. Handle the payment success event
    if payload.get("event") == "payment.succeeded":
        # Extract the email safely
        customer_data = payload.get("data", {}).get("customer", {})
        customer_email = customer_data.get("email")
        
        if customer_email:
            print(f"💰 PAYMENT RECEIVED FROM: {customer_email}")
            
            # 4. Find the user in the PostgreSQL database
            user = db.query(models.User).filter(models.User.email == customer_email).first()
            
            if user:
                # 5. Upgrade their account (1-year pass)
                user.has_paid = True
                user.access_valid_until = datetime.datetime.utcnow() + datetime.timedelta(days=365)
                
                # Save changes to the database
                db.commit()
                print(f"✅ ACCOUNT UPGRADED FOR: {customer_email}")
            else:
                print(f"⚠️ Warning: Payment received, but no user found with email {customer_email}")
                
    return {"status": "success"}