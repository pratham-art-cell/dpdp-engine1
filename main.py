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

@app.get("/blog/new", response_class=HTMLResponse)
async def blog_studio(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="blog_studio.html",
        context={"request": request}
    )

@app.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_detail(request: Request, slug: str):
    articles = get_articles()
    article = next((a for a in articles if a["slug"] == slug), None)
    if not article:
        return HTMLResponse(content="<h1>Article Not Found</h1>", status_code=404)
    return templates.TemplateResponse(
        request=request,
        name="blog_detail.html",
        context={"request": request, "article": article}
    )