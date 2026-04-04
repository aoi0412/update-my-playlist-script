from fastapi import APIRouter, UploadFile, File, HTTPException
import os
from pathlib import Path
from pydantic import BaseModel

from backend.config import settings

router = APIRouter(prefix="/api/settings", tags=["settings"])

class DirectoryCreate(BaseModel):
    name: str

COOKIES_FILE_PATH = Path("./data/cookies.txt")

@router.post("/cookies")
async def upload_cookies(file: UploadFile = File(...)):
    """Upload cookies.txt file for yt-dlp authentication."""
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are allowed")
    
    try:
        # Save to ./data/cookies.txt
        COOKIES_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        contents = await file.read()
        
        with open(COOKIES_FILE_PATH, "wb") as f:
            f.write(contents)
            
        return {"message": "Cookies file uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

@router.get("/cookies/status")
def get_cookies_status():
    """Check if cookies.txt exists."""
    return {"exists": COOKIES_FILE_PATH.exists()}

@router.get("/directories")
def get_directories():
    """Get list of available download directories."""
    base_dir = Path(settings.download_dir)
    directories = []
    if base_dir.exists():
        for path in base_dir.rglob('*'):
            if path.is_dir() and not path.name.startswith('.'):
                directories.append(str(path))
    
    # Always include the base directory
    result = [str(base_dir)] + directories
    # Return unique sorted directories
    return {"directories": sorted(list(set(result)))}

@router.post("/directories")
def create_directory(data: DirectoryCreate):
    """Create a new download directory."""
    if ".." in data.name or data.name.startswith("/") or data.name.startswith("\\"):
        raise HTTPException(status_code=400, detail="Invalid directory name")
        
    base_dir = Path(settings.download_dir)
    new_dir = base_dir / data.name
    
    try:
        new_dir.mkdir(parents=True, exist_ok=True)
        return {"directory": str(new_dir)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create directory: {str(e)}")
