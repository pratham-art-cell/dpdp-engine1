import json
import os
import jwt
from fastapi import FastAPI, Request, Depends, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy.orm import Session

from database import engine, Base, get_db, init_db
from config import settings
import models
from routers import auth, leads, labs, webhooks, api

init_db()

app = FastAPI(title="ConsentLayer DPDP Engine", version="1.0.0")

origins = [origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

class CachedStaticFiles(StaticFiles):
    def is_not_modified(self, response_headers, request_headers):
        response_headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return super().is_not_modified(response_headers, request_headers)

app.mount("/static", CachedStaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth.router)
app.include_router(leads.router)
app.include_router(labs.router)
app.include_router(webhooks.router)
app.include_router(api.router)

ARTICLES_FILE = os.path.join(os.path.dirname(__file__), "data", "longtail_articles.json")
CACHED_ARTICLES = []
if os.path.exists(ARTICLES_FILE):
    with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
        CACHED_ARTICLES = json.load(f)

def get_articles():
    return CACHED_ARTICLES

def get_current_user_safe(request: Request, db: Session):
    try:
        token = request.cookies.get("access_token")
        if not token:
            return None
        clean_token = token.replace("Bearer ", "").strip()
        payload = jwt.decode(clean_token, settings.secret_key, algorithms=[settings.algorithm])
        user_email = payload.get("sub")
        if not user_email:
            return None
        return db.query(models.User).filter(models.User.email == user_email).first()
    except jwt.PyJWTError:
        return None

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def home_page(request: Request, db: Session = Depends(get_db)):
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

@app.get("/about", response_class=HTMLResponse)
def about_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_safe(request, db)
    return templates.TemplateResponse(
        request=request, name="about.html", context={"request": request, "user": user, "has_paid": user.has_paid if user else False}
    )

@app.get("/support", response_class=HTMLResponse)
def support_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_safe(request, db)
    return templates.TemplateResponse(
        request=request, name="support.html", context={"request": request, "user": user, "has_paid": user.has_paid if user else False}
    )

@app.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_safe(request, db)
    return templates.TemplateResponse(
        request=request, name="reports.html", context={"request": request, "user": user, "has_paid": user.has_paid if user else False}
    )

@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_safe(request, db)
    return templates.TemplateResponse(
        request=request, name="settings.html", context={"request": request, "user": user, "has_paid": user.has_paid if user else False}
    )

@app.get("/blog", response_class=HTMLResponse)
def blog_index(request: Request):
    articles = get_articles()
    return templates.TemplateResponse(
        request=request, name="blog_index.html", context={"request": request, "articles": articles}
    )

@app.get("/blog/{slug}", response_class=HTMLResponse)
def blog_detail(request: Request, slug: str):
    static_templates = {
        "dpdp-section-5-notice-pathology": "blog_section_5_notice.html",
        "whatsapp-medical-reports-dpdp-compliance": "blog_whatsapp_compliance.html",
        "dpdp-act-healthcare-compliance-guide": "blog_dpdp_master_guide.html"
    }
    
    if slug in static_templates and os.path.exists(os.path.join("templates", static_templates[slug])):
        return templates.TemplateResponse(
            request=request, name=static_templates[slug], context={"request": request}
        )

    articles = get_articles()
    article = next((a for a in articles if a.get("slug") == slug), None)
    if article:
        return templates.TemplateResponse(
            request=request, name="blog_detail.html", context={"request": request, "article": article}
        )

    return HTMLResponse(
        content="<div style='text-align:center; padding:80px;'><h1>404 Article Not Found</h1></div>", 
        status_code=404
    )

@app.get("/robots.txt", response_class=Response)
def robots_txt():
    content = "User-agent: *\nAllow: /\nDisallow: /settings\nDisallow: /reports\n\nSitemap: https://consentlayers.in/sitemap.xml\n"
    return Response(content=content, media_type="text/plain")

@app.get("/sitemap.xml", response_class=Response)
def sitemap_xml():
    articles = get_articles()
    urls = [
        "https://consentlayers.in/",
        "https://consentlayers.in/about",
        "https://consentlayers.in/blog",
        "https://consentlayers.in/support",
        "https://consentlayers.in/login"
    ]
    for article in articles:
        if "slug" in article:
            urls.append(f"https://consentlayers.in/blog/{article['slug']}")
            
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml_content += f"  <url>\n    <loc>{url}</loc>\n    <changefreq>weekly</changefreq>\n  </url>\n"
    xml_content += '</urlset>'
    return Response(content=xml_content, media_type="application/xml")