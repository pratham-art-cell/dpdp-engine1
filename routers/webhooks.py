from fastapi import APIRouter, Request, HTTPException, Header
from config import settings

router = APIRouter(prefix="/webhooks", tags=["Billing"])

@router.post("/dodo")
async def dodo_payment_handler(request: Request, x_signature: str | None = Header(None)):
    # 1. Security Check: Ensure the request actually came from Dodo Payments
    if not x_signature:
        raise HTTPException(status_code=401, detail="Missing signature header")
        
    # 2. Parse the webhook payload
    payload = await request.json()
    
    # 3. Handle the payment success event
    if payload.get("event") == "payment.succeeded":
        customer_email = payload["data"]["customer"]["email"]
        # In Phase 3, you will update the database here to unlock their account
        print(f"💰 PAYMENT RECEIVED FROM: {customer_email}")
        
    return {"status": "success"}