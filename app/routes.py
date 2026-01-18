"""
API routes for MapToPostcard web app.
"""
import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.renderer import create_postcard, get_coordinates

router = APIRouter()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
THEMES_DIR = PROJECT_ROOT / "themes"
POSTCARDS_DIR = Path(__file__).parent / "static" / "postcards"


class PostcardRequest(BaseModel):
    city: str
    country: str
    theme: str = "warm_beige"
    distance: int = 8000
    message: str = ""
    fast: bool = True  # Default to fast mode


@router.get("/api/themes")
async def list_themes():
    """List all available themes with their details."""
    themes = []

    if not THEMES_DIR.exists():
        return {"themes": []}

    for theme_file in sorted(THEMES_DIR.glob("*.json")):
        theme_name = theme_file.stem
        try:
            with open(theme_file, 'r') as f:
                theme_data = json.load(f)
                themes.append({
                    "id": theme_name,
                    "name": theme_data.get("name", theme_name),
                    "description": theme_data.get("description", ""),
                    "colors": {
                        "bg": theme_data.get("bg", "#FFFFFF"),
                        "text": theme_data.get("text", "#000000"),
                        "water": theme_data.get("water", "#C0C0C0"),
                        "parks": theme_data.get("parks", "#F0F0F0"),
                        "road_primary": theme_data.get("road_primary", "#333333")
                    }
                })
        except Exception:
            continue

    return {"themes": themes}


@router.post("/api/generate")
def generate_postcard(request: PostcardRequest):
    """Generate a postcard image."""
    # Validate theme exists
    theme_file = THEMES_DIR / f"{request.theme}.json"
    if not theme_file.exists():
        raise HTTPException(status_code=400, detail=f"Theme '{request.theme}' not found")

    # Load theme
    with open(theme_file, 'r') as f:
        theme = json.load(f)

    try:
        # Get coordinates
        coords = get_coordinates(request.city, request.country)

        # Generate postcard
        image_bytes = create_postcard(
            city=request.city,
            country=request.country,
            point=coords,
            dist=request.distance,
            theme=theme,
            message=request.message,
            fast=request.fast
        )

        # Save to file
        POSTCARDS_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        city_slug = request.city.lower().replace(' ', '_').replace("'", "")
        filename = f"{city_slug}_{request.theme}_{timestamp}.png"
        filepath = POSTCARDS_DIR / filename

        with open(filepath, 'wb') as f:
            f.write(image_bytes)

        return {
            "success": True,
            "filename": filename,
            "url": f"/static/postcards/{filename}"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate postcard: {str(e)}")


@router.get("/postcards/{filename}")
async def get_postcard(filename: str):
    """Serve a generated postcard image."""
    filepath = POSTCARDS_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Postcard not found")
    return FileResponse(filepath, media_type="image/png")
