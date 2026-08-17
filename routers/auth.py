import datetime
import jwt
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
import models

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-super-secret-development-key"
ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# --- DUAL-PATHED AUTH ROUTES (GET & POST) ---

@router.get("/login", response_class=HTMLResponse)
@router.get("/auth/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@router.get("/signup", response_class=HTMLResponse)
@router.get("/auth/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


@router.post("/login")
@router.post("/auth/login")
async def login(
    email: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    normalized_email = email.strip().lower()
    user = db.query(models.User).filter(models.User.email == normalized_email).first()
    
    if not user or not verify_password(password, user.hashed_password):
        return RedirectResponse(url="/login?error=1", status_code=302)
    
    token = create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=604800)
    return response


@router.post("/signup")
@router.post("/auth/signup")
async def signup(
    email: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    normalized_email = email.strip().lower()
    existing_user = db.query(models.User).filter(models.User.email == normalized_email).first()
    
    if existing_user:
        return RedirectResponse(url="/login?error=exists", status_code=302)
    
    new_user = models.User(email=normalized_email, hashed_password=get_password_hash(password))
    db.add(new_user)
    db.commit()
    
    token = create_access_token(data={"sub": new_user.email})
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=604800)
    return response


@router.get("/logout")
@router.get("/auth/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response