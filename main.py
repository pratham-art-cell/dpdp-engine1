import json
import os
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from database import engine, Base, get_db
import models
from routers import auth, leads, labs

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ConsentLayer DPDP Engine", version="1.0.0")

# Mount Static Directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates Configuration
templates = Jinja2Templates(directory="templates")

# Register API Routers
app.include_router(auth.router)
app.include_router(leads.router)
app.include_router(labs.router)

# Load Programmatic SEO Dataset
def get_articles():
    file_path = os.path.join(os.path.dirname(__file__), "data", "longtail_articles.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def get_current_user_safe(request: Request, db: Session):
    try:
        token = request.cookies.get("access_token")
        if not token:
            return None
        
        # Strip Bearer prefix if present
        clean_token = token.replace("Bearer ", "").strip()
        
        # Strictly only search for the user's actual token
        user = db.query(models.User).filter(models.User.email == clean_token).first()
        return user
    except Exception:
        return None

# --- PUBLIC & DASHBOARD ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_safe(request, db)
    return templates.TemplateResponse(
        request=request,
        name="index.html", 
        context={
            "request": request, 
            "user": user,
            "user_email": user.email if user else None,
            "has_paid": user.has_paid if user else False,
            "is_active": user.is_active if user else False
        }
    )

@app.get("/support", response_class=HTMLResponse)
async def support_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_safe(request, db)
    return templates.TemplateResponse(
        request=request,
        name="support.html",
        context={"request": request, "user": user, "has_paid": user.has_paid if user else False}
    )

@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_safe(request, db)
    return templates.TemplateResponse(
        request=request,
        name="reports.html",
        context={"request": request, "user": user, "has_paid": user.has_paid if user else False}
    )

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_safe(request, db)
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={"request": request, "user": user, "has_paid": user.has_paid if user else False}
    )

@app.get("/blog", response_class=HTMLResponse)
async def blog_index(request: Request):
    articles = get_articles()
    return templates.TemplateResponse(
        request=request,
        name="blog_index.html",
        context={"request": request, "articles": articles}
    )

@app.get("/blog/new", response_class=HTMLResponse)
async def blog_studio(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="blog_editor.html",
        context={"request": request}
    )

@app.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_detail(request: Request, slug: str):
    static_templates = {
        "dpdp-section-5-notice-pathology": "blog_section_5_notice.html",
        "section-5-notice-template": "blog_section_5_notice.html",
        "whatsapp-medical-reports-dpdp-compliance": "blog_whatsapp_compliance.html",
        "whatsapp-compliance-clinics": "blog_whatsapp_compliance.html",
        "dpdp-act-healthcare-compliance-guide": "blog_dpdp_master_guide.html",
        "dpdp-act-healthcare-master-guide": "blog_dpdp_master_guide.html"
    }
    
    if slug in static_templates and os.path.exists(os.path.join("templates", static_templates[slug])):
        return templates.TemplateResponse(
            request=request,
            name=static_templates[slug],
            context={"request": request}
        )

    articles = get_articles()
    article = next((a for a in articles if a.get("slug") == slug), None)
    if article:
        return templates.TemplateResponse(
            request=request,
            name="blog_detail.html",
            context={"request": request, "article": article}
        )

    return HTMLResponse(
        content="""
        <div style="text-align:center; padding:80px 20px; font-family:sans-serif; background:#fcfdfd; min-height:100vh;">
            <h1 style="font-size:2rem; font-weight:800; color:#0f172a; margin-bottom:12px;">Article Not Found</h1>
            <p style="color:#64748b; margin-bottom:24px;">The compliance guide you requested could not be located.</p>
            <a href="/blog" style="display:inline-block; padding:10px 20px; background:#4f46e5; color:#ffffff; font-weight:700; text-decoration:none; border-radius:12px;">Return to Compliance Library</a>
        </div>
        """, 
        status_code=404
    )