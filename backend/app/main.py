"""
ViralClips AI — Main FastAPI Application
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger
from sqlalchemy import select

from app.config import get_settings
from app.database.session import init_db, get_db, AsyncSession
from app.database.models import Project, User, JobStatus
from app.auth.firebase_auth import get_current_user, get_optional_user, FirebaseUser
from app.workers.tasks import process_video_pipeline

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events: startup and shutdown."""
    # Startup
    logger.info("Initializing ViralClips AI Backend...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down ViralClips AI Backend...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)


# ── Middleware ──────────────────────────────────────────


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming requests and response status."""
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


# ── Exception Handlers ──────────────────────────────────


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global catch-all for unhandled exceptions."""
    logger.error(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error. Please try again later."},
    )


# ── Schemas ─────────────────────────────────────────────


class VideoRequest(BaseModel):
    url: str


class ProjectResponse(BaseModel):
    id: str
    title: str
    status: str
    progress_percent: int
    error_message: str | None


# ── Routes ──────────────────────────────────────────────


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Deep health check verifying DB connectivity."""
    try:
        # Ping the DB
        await db.execute(select(1))
        db_status = "ok"
    except Exception as e:
        logger.error(f"DB Health check failed: {e}")
        db_status = "error"

    if db_status != "ok":
        raise HTTPException(status_code=503, detail="Service Unavailable")

    return {
        "status": "ok",
        "database": db_status,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/api/v1/projects", response_model=list[ProjectResponse])
async def list_projects(
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all projects for the authenticated user."""
    # Ensure user exists in our DB
    result = await db.execute(select(User).where(User.id == user.uid))
    db_user = result.scalar_one_or_none()
    
    if not db_user:
        # Auto-create user profile on first login
        db_user = User(
            id=user.uid,
            email=user.email,
            display_name=user.name,
            photo_url=user.photo_url,
        )
        db.add(db_user)
        await db.commit()

    # Fetch projects
    result = await db.execute(
        select(Project)
        .where(Project.user_id == user.uid)
        .order_by(Project.created_at.desc())
        .limit(50)
    )
    projects = result.scalars().all()

    return [
        ProjectResponse(
            id=p.id,
            title=p.title or "Processing...",
            status=p.status,
            progress_percent=p.progress_percent,
            error_message=p.error_message,
        )
        for p in projects
    ]


@app.post("/api/v1/process")
async def process_video(
    request: VideoRequest,
    background_tasks: BackgroundTasks,
    user: FirebaseUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a video for AI processing."""
    if not request.url:
        raise HTTPException(status_code=400, detail="URL is required")

    logger.info(f"Processing request for URL: {request.url} | User: {user.uid}")

    # Ensure user exists
    user_result = await db.execute(select(User).where(User.id == user.uid))
    db_user = user_result.scalar_one_or_none()
    if not db_user:
        db_user = User(id=user.uid, email=user.email)
        db.add(db_user)

    # Check credits
    if db_user.credits_remaining <= 0 and db_user.plan == "free":
        raise HTTPException(
            status_code=402,
            detail="Insufficient credits. Please upgrade your plan.",
        )

    # Deduct credit
    db_user.credits_remaining -= 1

    # Create project record
    project = Project(
        user_id=user.uid,
        source_url=request.url,
        title="Extracting...",
        status=JobStatus.PENDING,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    # Dispatch to background task (Lightweight alternative to Celery)
    # For a high-scale production app, we would push this to RabbitMQ/Redis
    # and have Celery workers pick it up. For now, BackgroundTasks ensures
    # we don't block the HTTP response.
    background_tasks.add_task(
        process_video_pipeline,
        project_id=project.id,
        url=request.url,
        user_id=user.uid,
    )

    return {
        "project_id": project.id,
        "status": "queued",
        "message": "Video is being processed",
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=settings.DEBUG)
