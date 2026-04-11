from datetime import datetime
from pydantic import BaseModel


class TrackResponse(BaseModel):
    id: int
    playlist_id: int
    external_id: str
    title: str
    artist: str | None
    duration_seconds: int | None
    thumbnail_url: str | None
    first_seen_at: datetime

    class Config:
        from_attributes = True


class DownloadHistoryResponse(BaseModel):
    id: int
    track_id: int
    status: str
    file_path: str | None
    file_size_bytes: int | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class TrackWithPlaylist(TrackResponse):
    playlist_name: str


class DownloadHistoryWithTrack(DownloadHistoryResponse):
    track: TrackWithPlaylist | None = None


class DownloadStats(BaseModel):
    total_downloads: int
    completed_downloads: int
    failed_downloads: int
    pending_downloads: int
    total_file_size_bytes: int


class TrackSimple(BaseModel):
    id: int
    playlist_id: int
    external_id: str
    title: str
    artist: str | None
    first_seen_at: datetime

    class Config:
        from_attributes = True


class IncompleteDownloadsResponse(BaseModel):
    failed: list[DownloadHistoryWithTrack]
    file_missing: list[DownloadHistoryWithTrack]
    never_downloaded: list[TrackSimple]
    total_count: int


class RedownloadResult(BaseModel):
    retried_failed_count: int
    retried_file_missing_count: int
    retried_never_downloaded_count: int
    total_retried: int
