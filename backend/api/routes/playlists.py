from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from backend.db import get_db, Playlist
from backend.api.schemas import (
    PlaylistCreate,
    PlaylistUpdate,
    PlaylistResponse,
    PlaylistWithTracks,
)
from backend.services import PlaylistService, DownloadService

router = APIRouter(prefix="/api/playlists", tags=["playlists"])


def playlist_to_response(playlist: Playlist) -> dict:
    """Convert Playlist model to response dict"""
    return {
        "id": playlist.id,
        "url": playlist.url,
        "name": playlist.name,
        "platform": playlist.platform,
        "check_interval_hours": playlist.check_interval_hours,
        "is_active": playlist.is_active,
        "last_checked_at": playlist.last_checked_at,
        "created_at": playlist.created_at,
        "updated_at": playlist.updated_at,
        "track_count": len(playlist.tracks),
    }


@router.get("", response_model=list[PlaylistResponse])
def get_playlists(db: Session = Depends(get_db)):
    """Get all playlists"""
    playlists = db.query(Playlist).order_by(Playlist.created_at.desc()).all()
    return [playlist_to_response(p) for p in playlists]


@router.post("", response_model=PlaylistResponse, status_code=201)
def create_playlist(data: PlaylistCreate, db: Session = Depends(get_db)):
    """Create a new playlist"""
    # Check if URL already exists
    existing = db.query(Playlist).filter(Playlist.url == data.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Playlist URL already exists")

    service = PlaylistService(db)
    playlist = service.create_playlist(
        url=data.url,
        name=data.name,
        check_interval_hours=data.check_interval_hours,
    )

    if not playlist:
        raise HTTPException(
            status_code=400,
            detail="Failed to create playlist. Please check the URL is valid.",
        )

    return playlist_to_response(playlist)


@router.get("/{playlist_id}", response_model=PlaylistWithTracks)
def get_playlist(playlist_id: int, db: Session = Depends(get_db)):
    """Get playlist details with tracks"""
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    response = playlist_to_response(playlist)
    response["tracks"] = playlist.tracks
    return response


@router.put("/{playlist_id}", response_model=PlaylistResponse)
def update_playlist(
    playlist_id: int, data: PlaylistUpdate, db: Session = Depends(get_db)
):
    """Update playlist settings"""
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    if data.name is not None:
        playlist.name = data.name
    if data.check_interval_hours is not None:
        playlist.check_interval_hours = data.check_interval_hours
    if data.is_active is not None:
        playlist.is_active = data.is_active

    db.commit()
    db.refresh(playlist)
    return playlist_to_response(playlist)


@router.delete("/{playlist_id}", status_code=204)
def delete_playlist(playlist_id: int, db: Session = Depends(get_db)):
    """Delete a playlist"""
    service = PlaylistService(db)
    if not service.delete_playlist(playlist_id):
        raise HTTPException(status_code=404, detail="Playlist not found")


@router.post("/{playlist_id}/check", response_model=dict)
def check_playlist_updates(
    playlist_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Manually trigger playlist update check"""
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    playlist_service = PlaylistService(db)
    new_tracks = playlist_service.check_for_updates(playlist)

    # Download new tracks in background
    if new_tracks:
        download_service = DownloadService(db)
        background_tasks.add_task(download_service.download_new_tracks, new_tracks)

    return {
        "message": f"Found {len(new_tracks)} new tracks",
        "new_tracks": [{"id": t.id, "title": t.title} for t in new_tracks],
    }
