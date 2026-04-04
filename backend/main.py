import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db import engine, Base
from backend.db.migrations import run_migrations
from backend.api.routes import playlists_router, downloads_router, scheduler_router, settings_router
from backend.scheduler import setup_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Run migrations to fix older database schemas
run_migrations()

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Playlist Downloader",
    description="YouTube Music & SoundCloud playlist monitoring and download service",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://yt-dlp.tamao.tech",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(playlists_router)
app.include_router(downloads_router)
app.include_router(scheduler_router)
app.include_router(settings_router)

# Setup scheduler
setup_scheduler(app)


@app.get("/")
def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Playlist Downloader API"}


@app.get("/api/health")
def health_check():
    """API health check"""
    return {"status": "healthy"}
