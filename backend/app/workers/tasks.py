"""
Video processing pipeline — orchestrates the full workflow.
Uses FastAPI BackgroundTasks for async processing.
Can be extended with Celery when Redis is available.
"""

import os
import traceback
from pathlib import Path
from loguru import logger

from app.config import get_settings
from app.database.session import AsyncSessionLocal
from app.database.models import Project, Clip, JobStatus, ClipStatus, User
from app.video.downloader import downloader
from app.video.transcriber import transcriber
from app.video.renderer import renderer
from app.ai.gemini_service import gemini_service
from app.subtitles.generator import generate_clip_subtitles

from sqlalchemy import select

settings = get_settings()


async def _update_project_status(
    project_id: str, status: JobStatus, progress: int = None, error: str = None
):
    """Update project status in database."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if project:
            project.status = status
            if progress is not None:
                project.progress_percent = progress
            if error:
                project.error_message = error
            await session.commit()


async def process_video_pipeline(project_id: str, url: str, user_id: str):
    """
    Full video processing pipeline:
    1. Download video from YouTube
    2. Transcribe audio with Whisper
    3. Analyze transcript with Gemini AI
    4. Generate subtitles for each clip
    5. Render clips with subtitle burn-in
    6. Update database with results
    """

    async def progress(percent: int, status_str: str):
        """Progress callback for pipeline stages."""
        status_map = {
            "downloading": JobStatus.DOWNLOADING,
            "transcribing": JobStatus.TRANSCRIBING,
            "analyzing": JobStatus.ANALYZING,
            "clipping": JobStatus.CLIPPING,
            "rendering": JobStatus.RENDERING,
        }
        await _update_project_status(
            project_id,
            status_map.get(status_str, JobStatus.PENDING),
            percent,
        )

    try:
        logger.info(f"[Pipeline] Starting for project {project_id}")

        # ── 1. Download ──────────────────────────────────
        await progress(5, "downloading")
        download_result = await downloader.download(url, project_id, progress)

        # Update project with video info
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()
            if project:
                project.title = download_result["title"]
                project.source_file_path = download_result["file_path"]
                project.duration_seconds = download_result["duration"]
                await session.commit()

        # ── 2. Transcribe ────────────────────────────────
        await progress(20, "transcribing")
        transcript_result = await transcriber.transcribe(
            download_result["file_path"], progress
        )

        # Save transcript to project
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()
            if project:
                project.transcript = transcript_result["full_text"]
                await session.commit()

        # ── 3. AI Analysis ───────────────────────────────
        await progress(45, "analyzing")
        clip_candidates = await gemini_service.analyze_transcript(
            transcript_result["timestamped_transcript"],
            max_clips=10,
        )

        if not clip_candidates:
            logger.warning(f"[Pipeline] No clips found for project {project_id}")
            await _update_project_status(project_id, JobStatus.COMPLETED, 100)
            return

        logger.info(f"[Pipeline] AI found {len(clip_candidates)} clip candidates")

        # ── 4. Generate clips ────────────────────────────
        await progress(55, "clipping")

        clips_created = []
        output_dir = Path(settings.TEMP_DIR) / project_id / "clips"
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, candidate in enumerate(clip_candidates):
            try:
                clip_id_short = f"clip_{i:03d}"

                # Generate subtitles for this clip
                sub_path = str(output_dir / f"{clip_id_short}.ass")
                generate_clip_subtitles(
                    words=transcript_result.get("words", []),
                    clip_start=candidate["start_time"],
                    clip_end=candidate["end_time"],
                    output_path=sub_path,
                )

                # Render the clip with subtitle burn-in
                clip_output = str(output_dir / f"{clip_id_short}.mp4")
                await renderer.render_vertical(
                    source_path=download_result["file_path"],
                    output_path=clip_output,
                    start_time=candidate["start_time"],
                    end_time=candidate["end_time"],
                    subtitle_path=sub_path,
                )

                # Save clip to database
                async with AsyncSessionLocal() as session:
                    clip = Clip(
                        project_id=project_id,
                        title=candidate["title"],
                        hook=candidate.get("hook", ""),
                        start_time=candidate["start_time"],
                        end_time=candidate["end_time"],
                        duration=candidate["end_time"] - candidate["start_time"],
                        viral_score=candidate["viral_score"],
                        viral_reason=candidate.get("viral_reason", ""),
                        status=ClipStatus.COMPLETED,
                        output_path=clip_output,
                        subtitle_path=sub_path,
                    )
                    session.add(clip)
                    await session.commit()
                    clips_created.append(clip.id)

                # Update progress
                clip_progress = 55 + int((i + 1) / len(clip_candidates) * 40)
                await progress(clip_progress, "rendering")

            except Exception as e:
                logger.error(f"[Pipeline] Clip {i} failed: {e}")
                continue

        # ── 5. Complete ──────────────────────────────────
        await _update_project_status(project_id, JobStatus.COMPLETED, 100)
        logger.info(
            f"[Pipeline] Complete: {len(clips_created)}/{len(clip_candidates)} clips "
            f"rendered for project {project_id}"
        )

    except Exception as e:
        error_msg = str(e)[:500]
        logger.error(f"[Pipeline] FAILED for project {project_id}: {error_msg}")
        logger.error(traceback.format_exc())
        await _update_project_status(project_id, JobStatus.FAILED, error=error_msg)
