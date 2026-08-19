import json
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from database import engine, Base
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

# --- PUBLIC ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    user_email = request.cookies.get("access_token")
    return templates.TemplateResponse(
        request=request,
        name="index.html", 
        context={"request": request, "user_email": "clinic-admin@diagnostic.in" if user_email else None}
    )

@app.get("/support", response_class=HTMLResponse)
async def support_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="support.html",
        context={"request": request}
    )

@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="reports.html",
        context={"request": request}
    )

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={"request": request}
    )

@app.get("/blog", response_class=HTMLResponse)
async def blog_index(request: Request):
    articles = get_articles()
    return templates.TemplateResponse(
        request=request,
        name="blog_index.html",
        context={"request": request, "articles": articles}
    )

# Static creation studio route placed strictly BEFORE dynamic /blog/{slug}
@app.get("/blog/new", response_class=HTMLResponse)
async def blog_studio(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="blog_editor.html",
        context={"request": request}
    )

@app.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_detail(request: Request, slug: str):
    # Static legacy template mapping covering all variations
    static_templates = {
        # Section 5 Notice Templates
        "dpdp-section-5-notice-pathology": "blog_section_5_notice.html",
        "section-5-notice-template": "blog_section_5_notice.html",
        "dpdp-section-5-notice": "blog_section_5_notice.html",
        
        # WhatsApp Compliance Templates
        "whatsapp-medical-reports-dpdp-compliance": "blog_whatsapp_compliance.html",
        "whatsapp-compliance-clinics": "blog_whatsapp_compliance.html",
        "whatsapp-lab-report-dispatch": "blog_whatsapp_compliance.html",
        
        # Healthcare Master Guide
        "dpdp-act-healthcare-compliance-guide": "blog_dpdp_master_guide.html",
        "dpdp-act-healthcare-master-guide": "blog_dpdp_master_guide.html"
    }
    
    # 1. Check if a dedicated static template exists
    if slug in static_templates:
        template_name = static_templates[slug]
        if os.path.exists(os.path.join("templates", template_name)):
            return templates.TemplateResponse(
                request=request,
                name=template_name,
                context={"request": request}
            )

    # 2. Check programmatic JSON articles
    articles = get_articles()
    article = next((a for a in articles if a.get("slug") == slug), None)
    if article:
        return templates.TemplateResponse(
            request=request,
            name="blog_detail.html",
            context={"request": request, "article": article}
        )

    # 3. Fallback: Not Found
    return HTMLResponse(
        content="""
        <div style="text-align:center; padding:80px 20px; font-family:system-ui, -apple-system, sans-serif; background:#fcfdfd; min-height:100vh;">
            <h1 style="font-size:2rem; font-weight:800; color:#0f172a; margin-bottom:12px;">Article Not Found</h1>
            <p style="color:#64748b; font-size:0.95rem; margin-bottom:24px;">The compliance guide you requested could not be located.</p>
            <a href="/blog" style="display:inline-block; padding:10px 20px; background:#4f46e5; color:#ffffff; font-weight:700; text-decoration:none; border-radius:12px; font-size:0.875rem;">Return to Compliance Library</a>
        </div>
        """, 
        status_code=404
    )