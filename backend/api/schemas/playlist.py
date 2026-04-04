from datetime import datetime
from pydantic import BaseModel, HttpUrl, field_validator


class PlaylistBase(BaseModel):
    url: str
    name: str | None = None
    check_interval_hours: int = 24
    download_dir: str | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not (
            "youtube.com" in v
            or "music.youtube.com" in v
            or "soundcloud.com" in v
        ):
            raise ValueError("URL must be from YouTube, YouTube Music, or SoundCloud")
        return v


class PlaylistCreate(PlaylistBase):
    pass


class PlaylistUpdate(BaseModel):
    name: str | None = None
    check_interval_hours: int | None = None
    is_active: bool | None = None
    download_dir: str | None = None


class TrackBasic(BaseModel):
    id: int
    external_id: str
    title: str
    artist: str | None
    duration_seconds: int | None
    thumbnail_url: str | None
    first_seen_at: datetime

    class Config:
        from_attributes = True


class PlaylistResponse(BaseModel):
    id: int
    url: str
    name: str
    platform: str
    download_dir: str | None = None
    check_interval_hours: int
    is_active: bool
    last_checked_at: datetime | None
    created_at: datetime
    updated_at: datetime
    track_count: int = 0

    class Config:
        from_attributes = True


class PlaylistWithTracks(PlaylistResponse):
    tracks: list[TrackBasic] = []
