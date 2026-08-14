from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from database import init_db
from routers import labs, api, webhooks # IMPORT YOUR NEW ROUTERS

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="DPDP Audit Engine", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

# REGISTER ALL ROUTERS HERE
app.include_router(labs.router)
app.include_router(api.router)
app.include_router(webhooks.router)

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="index.html"
    )

