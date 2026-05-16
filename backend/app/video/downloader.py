"""
YouTube video downloader using yt-dlp.
Async subprocess wrapper with progress tracking.
"""

import asyncio
import os
import re
from pathlib import Path
from loguru import logger
from app.config import get_settings

settings = get_settings()


class VideoDownloader:
    """Downloads videos from YouTube via yt-dlp with progress tracking."""

    def __init__(self):
        self.temp_dir = Path(settings.TEMP_DIR)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def download(
        self,
        url: str,
        project_id: str,
        progress_callback=None,
    ) -> dict:
        """
        Download a video from YouTube.

        Args:
            url: YouTube video URL
            project_id: Unique project identifier for file naming
            progress_callback: async callable(percent: int, status: str)

        Returns:
            dict with keys: file_path, title, duration, thumbnail_url
        """
        output_dir = self.temp_dir / project_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / "source.%(ext)s")

        cmd = [
            "yt-dlp",
            "--no-playlist",
            "--merge-output-format", "mp4",
            "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "--output", output_path,
            "--print-json",
            "--no-warnings",
            "--max-filesize", f"{settings.MAX_UPLOAD_SIZE_MB}m",
            url,
        ]

        logger.info(f"Starting download: {url}")
        if progress_callback:
            await progress_callback(5, "downloading")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=600,  # 10 minute timeout
            )

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"yt-dlp failed: {error_msg}")
                raise RuntimeError(f"Download failed: {error_msg[:200]}")

            # Parse the JSON output from yt-dlp
            import json
            metadata = json.loads(stdout.decode().strip().split("\n")[-1])

            # Find the actual downloaded file
            downloaded_files = list(output_dir.glob("source.*"))
            if not downloaded_files:
                raise RuntimeError("Download completed but no file found")

            file_path = str(downloaded_files[0])
            result = {
                "file_path": file_path,
                "title": metadata.get("title", "Untitled"),
                "duration": metadata.get("duration", 0),
                "thumbnail_url": metadata.get("thumbnail", ""),
            }

            if progress_callback:
                await progress_callback(15, "downloading")

            logger.info(f"Downloaded: {result['title']} ({result['duration']}s)")
            return result

        except asyncio.TimeoutError:
            logger.error(f"Download timed out for {url}")
            raise RuntimeError("Download timed out after 10 minutes")

    async def cleanup(self, project_id: str):
        """Remove temporary files for a project."""
        import shutil
        project_dir = self.temp_dir / project_id
        if project_dir.exists():
            shutil.rmtree(project_dir, ignore_errors=True)
            logger.info(f"Cleaned up temp files for project {project_id}")


downloader = VideoDownloader()
