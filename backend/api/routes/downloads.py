from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
from backend.db import get_db, Track, DownloadHistory, Playlist
from backend.api.schemas.download import (
    DownloadHistoryResponse,
    DownloadHistoryWithTrack,
    DownloadStats,
    IncompleteDownloadsResponse,
    RedownloadResult,
)
from backend.services import DownloadService

router = APIRouter(prefix="/api/downloads", tags=["downloads"])


@router.get("", response_model=list[DownloadHistoryWithTrack])
def get_download_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    playlist_id: int | None = None,
    db: Session = Depends(get_db),
):
    """Get download history with optional filters"""
    service = DownloadService(db)
    history_list = service.get_download_history(
        limit=limit,
        offset=offset,
        status=status,
        playlist_id=playlist_id,
    )

    result = []
    for history in history_list:
        track = db.query(Track).filter(Track.id == history.track_id).first()
        playlist = db.query(Playlist).filter(Playlist.id == track.playlist_id).first() if track else None

        result.append({
            "id": history.id,
            "track_id": history.track_id,
            "status": history.status,
            "file_path": history.file_path,
            "file_size_bytes": history.file_size_bytes,
            "error_message": history.error_message,
            "started_at": history.started_at,
            "completed_at": history.completed_at,
            "created_at": history.created_at,
            "track": {
                "id": track.id,
                "playlist_id": track.playlist_id,
                "external_id": track.external_id,
                "title": track.title,
                "artist": track.artist,
                "duration_seconds": track.duration_seconds,
                "thumbnail_url": track.thumbnail_url,
                "first_seen_at": track.first_seen_at,
                "playlist_name": playlist.name if playlist else "Unknown",
            } if track else None,
        })

    return result


@router.get("/stats", response_model=DownloadStats)
def get_download_stats(db: Session = Depends(get_db)):
    """Get download statistics"""
    service = DownloadService(db)
    return service.get_download_stats()


@router.get("/{download_id}", response_model=DownloadHistoryResponse)
def get_download(download_id: int, db: Session = Depends(get_db)):
    """Get specific download history entry"""
    history = (
        db.query(DownloadHistory)
        .filter(DownloadHistory.id == download_id)
        .first()
    )
    if not history:
        raise HTTPException(status_code=404, detail="Download not found")
    return history


@router.post("/track/{track_id}", response_model=DownloadHistoryResponse)
def download_track(track_id: int, db: Session = Depends(get_db)):
    """Manually trigger download for a specific track"""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    service = DownloadService(db)
    history = service.download_track(track)
    return history


@router.post("/{download_id}/retry", response_model=DownloadHistoryResponse)
def retry_download(download_id: int, db: Session = Depends(get_db)):
    """Retry a failed download"""
    service = DownloadService(db)
    history = service.retry_failed_download(download_id)
    if not history:
        raise HTTPException(
            status_code=400,
            detail="Download not found or not in failed state",
        )
    return history


@router.get("/incomplete", response_model=IncompleteDownloadsResponse)
def get_incomplete_downloads(
    playlist_id: int | None = None,
    db: Session = Depends(get_db),
):
    """
    Get tracks with incomplete downloads:
    - failed: download failed with error
    - file_missing: completed but file no longer exists on disk
    - never_downloaded: tracks that were never downloaded
    """
    service = DownloadService(db)
    incomplete = service.get_incomplete_downloads()

    def build_history_with_track(history: DownloadHistory) -> dict:
        track = db.query(Track).filter(Track.id == history.track_id).first()
        playlist = db.query(Playlist).filter(Playlist.id == track.playlist_id).first() if track else None
        return {
            "id": history.id,
            "track_id": history.track_id,
            "status": history.status,
            "file_path": history.file_path,
            "file_size_bytes": history.file_size_bytes,
            "error_message": history.error_message,
            "started_at": history.started_at,
            "completed_at": history.completed_at,
            "created_at": history.created_at,
            "track": {
                "id": track.id,
                "playlist_id": track.playlist_id,
                "external_id": track.external_id,
                "title": track.title,
                "artist": track.artist,
                "duration_seconds": track.duration_seconds,
                "thumbnail_url": track.thumbnail_url,
                "first_seen_at": track.first_seen_at,
                "playlist_name": playlist.name if playlist else "Unknown",
            } if track else None,
        }

    failed = [
        build_history_with_track(h) for h in incomplete["failed"]
        if not playlist_id or (
            db.query(Track).filter(Track.id == h.track_id).first() is not None
            and db.query(Track).filter(Track.id == h.track_id).first().playlist_id == playlist_id
        )
    ]
    file_missing = [
        build_history_with_track(h) for h in incomplete["file_missing"]
        if not playlist_id or (
            db.query(Track).filter(Track.id == h.track_id).first() is not None
            and db.query(Track).filter(Track.id == h.track_id).first().playlist_id == playlist_id
        )
    ]
    never_downloaded = [
        t for t in incomplete["never_downloaded"]
        if not playlist_id or t.playlist_id == playlist_id
    ]

    return {
        "failed": failed,
        "file_missing": file_missing,
        "never_downloaded": never_downloaded,
        "total_count": len(failed) + len(file_missing) + len(never_downloaded),
    }


@router.post("/incomplete/redownload", response_model=RedownloadResult)
def redownload_incomplete(
    playlist_id: int | None = None,
    db: Session = Depends(get_db),
):
    """
    Re-download all incomplete tracks (failed, file missing, or never downloaded).
    Optionally filter by playlist_id.
    """
    service = DownloadService(db)
    result = service.redownload_incomplete(playlist_id=playlist_id)

    retried_failed = len(result["retried_failed"])
    retried_missing = len(result["retried_file_missing"])
    retried_never = len(result["retried_never_downloaded"])

    return {
        "retried_failed_count": retried_failed,
        "retried_file_missing_count": retried_missing,
        "retried_never_downloaded_count": retried_never,
        "total_retried": retried_failed + retried_missing + retried_never,
    }


@router.get("/files/{filename}")
def download_file(filename: str, db: Session = Depends(get_db)):
    """Download an MP3 file"""
    from backend.config import settings

    file_path = Path(settings.download_dir) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="audio/mpeg",
    )
