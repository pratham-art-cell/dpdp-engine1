from contextlib import asynccontextmanager
import os
import datetime
from fastapi import FastAPI, Request, Depends, Form
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, Response, PlainTextResponse
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
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# ==========================================
# SEO: SITEMAP & ROBOTS.TXT
# ==========================================
@app.get("/sitemap.xml", include_in_schema=False)
def get_sitemap():
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
       <url>
          <loc>https://consentlayers.in/</loc>
          <changefreq>daily</changefreq>
          <priority>1.0</priority>
       </url>
       <url>
          <loc>https://consentlayers.in/blog/dpdp-act-healthcare-compliance-guide</loc>
          <changefreq>weekly</changefreq>
          <priority>0.9</priority>
       </url>
       <url>
          <loc>https://consentlayers.in/blog</loc>
          <changefreq>weekly</changefreq>
          <priority>0.8</priority>
       </url>
       <url>
          <loc>https://consentlayers.in/login</loc>
          <changefreq>weekly</changefreq>
          <priority>0.8</priority>
       </url>
       <url>
          <loc>https://consentlayers.in/support</loc>
          <changefreq>monthly</changefreq>
          <priority>0.5</priority>
       </url>
    </urlset>
    """
    return Response(content=xml_content.strip(), media_type="application/xml")

@app.get("/robots.txt", include_in_schema=False)
def get_robots():
    robots_content = """User-agent: *
Allow: /
Allow: /blog
Allow: /blog/*
Disallow: /api/
Disallow: /settings
Disallow: /reports

Sitemap: https://consentlayers.in/sitemap.xml
"""
    return PlainTextResponse(content=robots_content)

# ==========================================
# PUBLIC BLOG ROUTES (No Authentication Required)
# ==========================================
@app.get("/blog/dpdp-act-healthcare-compliance-guide", response_class=HTMLResponse)
def read_dpdp_master_guide(request: Request):
    """
    Renders the public DPDP healthcare compliance master guide.
    """
    return templates.TemplateResponse(
        request=request,
        name="blog_dpdp_master_guide.html",
        context={"request": request}
    )

@app.get("/blog", response_class=HTMLResponse)
def blog_index(request: Request):
    """
    Direct alias for /blog.
    """
    return templates.TemplateResponse(
        request=request,
        name="blog_dpdp_master_guide.html",
        context={"request": request}
    )

# ==========================================
# ROUTERS
# ==========================================
app.include_router(labs.router)
app.include_router(api.router)
app.include_router(webhooks.router)
app.include_router(auth.router) 

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
# AUTHENTICATED / MAIN ROUTES
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

@app.get("/support", response_class=HTMLResponse)
def support_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user: 
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        request=request, 
        name="support.html", 
        context={"request": request, "user_email": user.email}
    )