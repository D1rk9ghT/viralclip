"""
FFmpeg-based video renderer for clip extraction and subtitle burn-in.
Uses async subprocess for non-blocking operation.
"""

import asyncio
import os
from pathlib import Path
from loguru import logger
from app.config import get_settings

settings = get_settings()


class VideoRenderer:
    """Renders clips from source video with subtitle burn-in."""

    async def extract_clip(
        self,
        source_path: str,
        output_path: str,
        start_time: float,
        end_time: float,
        subtitle_path: str = None,
        progress_callback=None,
    ) -> str:
        """
        Extract a clip from source video.

        Args:
            source_path: Path to full source video
            output_path: Where to write the rendered clip
            start_time: Start time in seconds
            end_time: End time in seconds
            subtitle_path: Optional ASS subtitle file to burn in
            progress_callback: async callable(percent, status)

        Returns:
            Path to the rendered clip file.
        """
        duration = end_time - start_time
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Build FFmpeg command
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-i", source_path,
            "-t", str(duration),
        ]

        # Video filters
        vf_filters = []

        # Subtitle burn-in
        if subtitle_path and os.path.exists(subtitle_path):
            # Escape path for FFmpeg filter syntax
            escaped_path = subtitle_path.replace("\\", "/").replace(":", "\\:")
            vf_filters.append(f"ass='{escaped_path}'")

        if vf_filters:
            cmd.extend(["-vf", ",".join(vf_filters)])

        # Encoding settings optimized for social media
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            "-threads", str(settings.FFMPEG_THREADS),
            "-movflags", "+faststart",  # Web-optimized MP4
            output_path,
        ])

        logger.info(f"Rendering clip: {start_time:.1f}s-{end_time:.1f}s → {output_path}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300,  # 5 minute timeout per clip
            )

            if process.returncode != 0:
                error = stderr.decode()[-500:]
                logger.error(f"FFmpeg failed: {error}")
                raise RuntimeError(f"Clip rendering failed: {error[:200]}")

            if not os.path.exists(output_path):
                raise RuntimeError("FFmpeg completed but output file not found")

            file_size = os.path.getsize(output_path)
            logger.info(f"Clip rendered: {output_path} ({file_size / 1024 / 1024:.1f}MB)")

            return output_path

        except asyncio.TimeoutError:
            logger.error("FFmpeg rendering timed out")
            raise RuntimeError("Rendering timed out after 5 minutes")

    async def render_vertical(
        self,
        source_path: str,
        output_path: str,
        start_time: float,
        end_time: float,
        width: int = 1080,
        height: int = 1920,
        subtitle_path: str = None,
    ) -> str:
        """
        Extract clip and scale/crop to vertical 9:16 format.
        Uses FFmpeg crop filter instead of OpenCV reframing for speed.
        """
        duration = end_time - start_time
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        vf_parts = [
            f"crop=ih*9/16:ih",  # Center crop to 9:16
            f"scale={width}:{height}",
        ]

        if subtitle_path and os.path.exists(subtitle_path):
            escaped = subtitle_path.replace("\\", "/").replace(":", "\\:")
            vf_parts.append(f"ass='{escaped}'")

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-i", source_path,
            "-t", str(duration),
            "-vf", ",".join(vf_parts),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-threads", str(settings.FFMPEG_THREADS),
            "-movflags", "+faststart",
            output_path,
        ]

        logger.info(f"Rendering vertical clip: {start_time:.1f}s-{end_time:.1f}s")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=300
        )

        if process.returncode != 0:
            error = stderr.decode()[-500:]
            raise RuntimeError(f"Vertical rendering failed: {error[:200]}")

        return output_path


renderer = VideoRenderer()
