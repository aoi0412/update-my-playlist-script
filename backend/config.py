from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/db/app.db"
    download_dir: str = "./data/downloads"
    youtube_cookies_file: str | None = None

    # Scheduler settings
    default_check_interval_hours: int = 24

    # yt-dlp settings
    audio_format: str = "mp3"
    audio_quality: str = "192"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure directories exist
Path(settings.download_dir).mkdir(parents=True, exist_ok=True)
db_path = Path(settings.database_url.replace("sqlite:///", "")).parent
db_path.mkdir(parents=True, exist_ok=True)
