from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from .database import Base


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(500), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)  # 'youtube_music' or 'soundcloud'
    download_dir = Column(String(500), nullable=True)
    check_interval_hours = Column(Integer, default=24)
    is_active = Column(Boolean, default=True)
    last_checked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tracks = relationship("Track", back_populates="playlist", cascade="all, delete-orphan")


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False)
    external_id = Column(String(255), nullable=False)  # Platform-specific ID
    title = Column(String(500), nullable=False)
    artist = Column(String(255), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    first_seen_at = Column(DateTime, default=datetime.utcnow)

    playlist = relationship("Playlist", back_populates="tracks")
    download_history = relationship("DownloadHistory", back_populates="track", cascade="all, delete-orphan")

    __table_args__ = (
        # Unique constraint on playlist_id + external_id
        {"sqlite_autoincrement": True},
    )


class DownloadHistory(Base):
    __tablename__ = "download_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(Integer, ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, downloading, completed, failed
    file_path = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    track = relationship("Track", back_populates="download_history")
