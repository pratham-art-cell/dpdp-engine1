import hmac
import hashlib
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
import models
from config import settings

router = APIRouter(prefix="/webhooks", tags=["Billing"])

# Product ID to Validity Days Mapping
TIER_DAYS_MAP = {
    "pdt_0NlfDkT4MTV8ryKRtX7C9": 30,    # 1 Month Tier (₹1,500)
    "pdt_0NlfDkOjRiEYe04Ob1gaQ": 90,    # 3 Months Tier (₹4,000)
    "pdt_0NlfDWjGRA2AdvNFU0oQm": 180,   # 6 Months Tier (₹7,500)
    "pdt_0NlfDkWXgi3I3vddp9vjM": 365,   # 1 Year Enterprise Tier (₹15,000)
}

@router.post("/dodo")
async def dodo_payment_handler(request: Request, db: Session = Depends(get_db)):
    signature = request.headers.get("webhook-signature") or request.headers.get("x-signature")
    
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature header")
        
    payload_body = await request.body()
    
    # Compute HMAC SHA256 signature
    expected_sig = hmac.new(
        settings.dodo_webhook_secret.encode("utf-8"), 
        payload_body, 
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
    payload = json.loads(payload_body)
    event_type = payload.get("event") or payload.get("type")
    
    if event_type == "payment.succeeded":
        data = payload.get("data", {})
        customer_data = data.get("customer", {})
        customer_email = customer_data.get("email")
        product_id = data.get("product_id")
        
        if customer_email:
            normalized_email = customer_email.strip().lower()
            user = db.query(models.User).filter(models.User.email == normalized_email).first()
            
            if user:
                duration_days = TIER_DAYS_MAP.get(product_id, 30)
                now = datetime.utcnow()
                base_time = user.access_valid_until if (user.access_valid_until and user.access_valid_until > now) else now
                
                user.has_paid = True
                user.access_valid_until = base_time + timedelta(days=duration_days)
                db.commit()
                
    return {"status": "success"}