"""
FastAPI application entry point for MapToPostcard web app.
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.routes import router

# Get the app directory path
APP_DIR = Path(__file__).parent
PROJECT_ROOT = APP_DIR.parent

app = FastAPI(
    title="Mapcard",
    description="Generate beautiful map postcards with personalized messages",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")

# Mount postcards output directory
postcards_dir = APP_DIR / "static" / "postcards"
postcards_dir.mkdir(exist_ok=True)

# Include API routes
app.include_router(router)

# Templates
templates = Jinja2Templates(directory=APP_DIR / "templates")


@app.get("/")
async def home(request: Request):
    """Serve the main page."""
    return templates.TemplateResponse("index.html", {"request": request})
