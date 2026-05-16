"""
SQLAlchemy database models for ViralClips AI.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, ForeignKey,
    Boolean, Enum, Index, JSON
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


# ── Enums ───────────────────────────────────────────────


class JobStatus(str, PyEnum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    CLIPPING = "clipping"
    RENDERING = "rendering"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ClipStatus(str, PyEnum):
    PENDING = "pending"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


# ── Models ──────────────────────────────────────────────


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    """Firebase-authenticated user profile."""
    __tablename__ = "users"

    id = Column(String(128), primary_key=True, doc="Firebase UID")
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    photo_url = Column(Text, nullable=True)
    plan = Column(String(50), default="free", nullable=False)
    credits_remaining = Column(Integer, default=3, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    """A video processing project (one source video → multiple clips)."""
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(128), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    source_url = Column(Text, nullable=True, doc="YouTube URL or upload path")
    source_file_path = Column(Text, nullable=True, doc="Path to downloaded source")
    duration_seconds = Column(Float, nullable=True)
    transcript = Column(Text, nullable=True)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    progress_percent = Column(Integer, default=0)
    metadata_ = Column("metadata", JSON, nullable=True, doc="Extra metadata as JSON")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="projects")
    clips = relationship("Clip", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_projects_user_status", "user_id", "status"),
    )


class Clip(Base):
    """An individual clip extracted from a project."""
    __tablename__ = "clips"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    hook = Column(Text, nullable=True, doc="Opening hook text")
    start_time = Column(Float, nullable=False, doc="Start time in seconds")
    end_time = Column(Float, nullable=False, doc="End time in seconds")
    duration = Column(Float, nullable=False)
    viral_score = Column(Integer, default=0, doc="AI-predicted virality 1-100")
    viral_reason = Column(Text, nullable=True)
    status = Column(Enum(ClipStatus), default=ClipStatus.PENDING, nullable=False)
    output_path = Column(Text, nullable=True, doc="GCS path to rendered clip")
    download_url = Column(Text, nullable=True)
    subtitle_path = Column(Text, nullable=True, doc="Path to ASS subtitle file")
    thumbnail_url = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    project = relationship("Project", back_populates="clips")

    __table_args__ = (
        Index("ix_clips_project_score", "project_id", "viral_score"),
    )
