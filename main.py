from contextlib import asynccontextmanager
import os
import json
import datetime
from pathlib import Path
from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, Response, PlainTextResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import jwt 

from database import init_db, get_db
import models
from routers import labs, api, webhooks, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="ConsentLayer DPDP Engine", lifespan=lifespan)

app.add_middleware(GZipMiddleware, minimum_size=1000)

os.makedirs("static", exist_ok=True)
os.makedirs("data", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Helper: Load Programmatic Articles
def get_dynamic_articles():
    data_path = Path("data/longtail_articles.json")
    if data_path.exists():
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

# ==========================================
# AUTH HELPER
# ==========================================
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
        
        if user and user.has_paid and user.access_valid_until:
            if datetime.datetime.utcnow() > user.access_valid_until:
                user.has_paid = False
                db.commit()
                
        return user
    except jwt.PyJWTError:
        return None

# ==========================================
# SEO & AI CRAWLER ROUTES
# ==========================================
@app.get("/sitemap.xml", include_in_schema=False)
def get_sitemap():
    # Core static endpoints
    urls = [
        {"loc": "https://consentlayers.in/", "priority": "1.0", "changefreq": "daily"},
        {"loc": "https://consentlayers.in/blog", "priority": "0.9", "changefreq": "weekly"},
        {"loc": "https://consentlayers.in/blog/dpdp-act-healthcare-compliance-guide", "priority": "0.9", "changefreq": "weekly"},
        {"loc": "https://consentlayers.in/blog/dpdp-section-5-notice-pathology", "priority": "0.8", "changefreq": "weekly"},
        {"loc": "https://consentlayers.in/blog/whatsapp-medical-reports-dpdp-compliance", "priority": "0.8", "changefreq": "weekly"},
        {"loc": "https://consentlayers.in/login", "priority": "0.8", "changefreq": "weekly"},
        {"loc": "https://consentlayers.in/support", "priority": "0.5", "changefreq": "monthly"}
    ]
    
    # Append dynamic long-tail post URLs
    for post in get_dynamic_articles():
        urls.append({
            "loc": f"https://consentlayers.in/blog/{post['slug']}",
            "priority": "0.7",
            "changefreq": "weekly"
        })
    
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        xml_content += f"""   <url>
      <loc>{u['loc']}</loc>
      <changefreq>{u['changefreq']}</changefreq>
      <priority>{u['priority']}</priority>
   </url>\n"""
    xml_content += '</urlset>'
    
    return Response(content=xml_content.strip(), media_type="application/xml")

@app.get("/robots.txt", include_in_schema=False)
def get_robots():
    robots_content = """User-agent: *
Allow: /
Allow: /blog
Allow: /blog/*
Allow: /llms.txt
Allow: /support
Disallow: /api/
Disallow: /settings
Disallow: /reports
Disallow: /blog/new

Sitemap: https://consentlayers.in/sitemap.xml
"""
    return PlainTextResponse(content=robots_content)

@app.get("/llms.txt", include_in_schema=False)
def get_llms_txt():
    return FileResponse("llms.txt", media_type="text/plain")

# ==========================================
# PUBLIC & BLOG ROUTES
# ==========================================
@app.get("/support", response_class=HTMLResponse)
def public_support_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    user_email = user.email if user else ""
    return templates.TemplateResponse(
        request=request, 
        name="support.html", 
        context={"request": request, "user_email": user_email}
    )

@app.get("/blog", response_class=HTMLResponse)
def blog_index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="blog_index.html",
        context={"request": request}
    )

@app.get("/blog/dpdp-act-healthcare-compliance-guide", response_class=HTMLResponse)
def read_dpdp_master_guide(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="blog_dpdp_master_guide.html",
        context={"request": request}
    )

@app.get("/blog/dpdp-section-5-notice-pathology", response_class=HTMLResponse)
def blog_section_5(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="blog_section_5_notice.html",
        context={"request": request}
    )

@app.get("/blog/whatsapp-medical-reports-dpdp-compliance", response_class=HTMLResponse)
def blog_whatsapp(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="blog_whatsapp_compliance.html",
        context={"request": request}
    )

# 1. Explicit /blog/new route must precede the dynamic catch-all route
@app.get("/blog/new", response_class=HTMLResponse)
def blog_editor_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        request=request, 
        name="blog_editor.html", 
        context={"request": request, "user_email": user.email}
    )

# 2. Dynamic Long-Tail Catch-All Route
@app.get("/blog/{slug}", response_class=HTMLResponse)
def dynamic_blog_post(slug: str, request: Request):
    articles = get_dynamic_articles()
    post = next((a for a in articles if a.get("slug") == slug), None)
    if not post:
        raise HTTPException(status_code=404, detail="Resource not found")
    return templates.TemplateResponse(
        request=request, 
        name="blog_dynamic_post.html", 
        context={"request": request, "article": post}
    )

# ==========================================
# ROUTERS
# ==========================================
app.include_router(labs.router)
app.include_router(api.router)
app.include_router(webhooks.router)
app.include_router(auth.router) 

# ==========================================
# AUTHENTICATED ROUTES
# ==========================================
@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"request": request, "has_paid": user.has_paid, "user_email": user.email}
    )

@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user: 
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        request=request, 
        name="settings.html", 
        context={
            "request": request, 
            "user_email": user.email,
            "user_full_name": user.full_name,
            "user_mobile": user.mobile,
            "user_address": user.address
        }
    )

@app.post("/settings/update", response_class=HTMLResponse)
def update_profile_settings(
    request: Request, 
    full_name: str = Form(""), 
    mobile: str = Form(""), 
    address: str = Form(""), 
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    if not user: 
        return HTMLResponse("Unauthorized", status_code=401)

    user.full_name = full_name
    user.mobile = mobile
    user.address = address
    db.commit()

    return HTMLResponse("""
    <div class="mt-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-lg flex items-center gap-2">
        <span>✅</span> Profile successfully updated in database.
    </div>
    """)

@app.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user: 
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        request=request, 
        name="reports.html", 
        context={"request": request, "user_email": user.email}
    )