import datetime
import jwt
import bcrypt
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from config import settings
import models

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="templates")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8')[:72], hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8')[:72], salt).decode('utf-8')

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

@router.get("/login", response_class=HTMLResponse)
@router.get("/auth/login", response_class=HTMLResponse)
@router.get("/signup", response_class=HTMLResponse)
@router.get("/auth/signup", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request})

@router.post("/login")
@router.post("/auth/login")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    normalized_email = email.strip().lower()
    user = db.query(models.User).filter(models.User.email == normalized_email).first()
    
    if not user or not verify_password(password, user.hashed_password):
        return RedirectResponse(url="/login?error=1", status_code=302)
    
    token = create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        key="access_token", 
        value=token, 
        httponly=True, 
        secure=not settings.debug, 
        samesite="lax", 
        max_age=604800
    )
    return response

@router.post("/signup")
@router.post("/auth/signup")
def signup(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if len(password) < 8:
        return RedirectResponse(url="/login?error=weak_password", status_code=302)

    normalized_email = email.strip().lower()
    existing_user = db.query(models.User).filter(models.User.email == normalized_email).first()
    
    if existing_user:
        return RedirectResponse(url="/login?error=exists", status_code=302)
    
    new_user = models.User(email=normalized_email, hashed_password=get_password_hash(password))
    db.add(new_user)
    db.commit()
    
    token = create_access_token(data={"sub": new_user.email})
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        key="access_token", 
        value=token, 
        httponly=True, 
        secure=not settings.debug, 
        samesite="lax", 
        max_age=604800
    )
    return response

@router.get("/logout")
@router.get("/auth/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response