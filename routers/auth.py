from fastapi import APIRouter, Depends, HTTPException, Response, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import jwt
import datetime

from database import get_db
import models
from config import settings

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="templates")

# Password Hashing Configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration (Use a strong secret key in production!)
SECRET_KEY = "your-super-secret-development-key"
ALGORITHM = "HS256"

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(days=7) # 7-day login session
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- ROUTES ---

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@router.post("/login")
async def login(response: Response, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        # In a real app, you'd return an error to the template. Redirecting for simplicity.
        return RedirectResponse(url="/login?error=1", status_code=302)
    
    # Generate Token and set Cookie
    token = create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=604800)
    return response

@router.post("/signup")
async def signup(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if existing_user:
        return RedirectResponse(url="/login?error=exists", status_code=302)
    
    # Create new user
    new_user = models.User(email=email, hashed_password=get_password_hash(password))
    db.add(new_user)
    db.commit()
    
    # Auto-login after signup
    token = create_access_token(data={"sub": new_user.email})
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=604800)
    return response

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response