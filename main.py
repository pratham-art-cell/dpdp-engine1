from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import jwt # New import

from database import init_db, get_db
import models
from routers import labs, api, webhooks, auth # Added auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="DPDP Audit Engine", lifespan=lifespan)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register all routers
app.include_router(labs.router)
app.include_router(api.router)
app.include_router(webhooks.router)
app.include_router(auth.router) # Register the auth router

templates = Jinja2Templates(directory="templates")

# Dependency to check current user
def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        user = db.query(models.User).filter(models.User.email == email).first()
        return user
    except jwt.PyJWTError:
        return None

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    
    # If not logged in, redirect to login page
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Render the dashboard with REAL user data from PostgreSQL!
    return templates.TemplateResponse(
        request=request, 
        name="index.html",
        context={
            "has_paid": user.has_paid,
            "user_email": user.email
        }
    )