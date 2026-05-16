"""
Video transcription using faster-whisper.
Produces word-level timestamps for subtitle synchronization.
"""

import asyncio
from pathlib import Path
from typing import Optional
from loguru import logger
from app.config import get_settings

settings = get_settings()


class Transcriber:
    """Whisper-based transcription with word-level timing."""

    def __init__(self):
        self._model = None

    def _load_model(self):
        """Lazy-load the whisper model to avoid startup overhead."""
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                settings.WHISPER_MODEL,
                device="cpu",
                compute_type="int8",
            )
            logger.info(f"Whisper model loaded: {settings.WHISPER_MODEL}")
        return self._model

    def _transcribe_sync(self, audio_path: str) -> dict:
        """
        Synchronous transcription (CPU-bound).
        Returns transcript with word-level timestamps.
        """
        model = self._load_model()

        segments, info = model.transcribe(
            audio_path,
            beam_size=5,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        words = []
        full_text_parts = []
        timestamped_lines = []

        for segment in segments:
            line_text = segment.text.strip()
            if not line_text:
                continue

            full_text_parts.append(line_text)
            timestamped_lines.append({
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": line_text,
            })

            if segment.words:
                for word in segment.words:
                    words.append({
                        "word": word.word.strip(),
                        "start": round(word.start, 2),
                        "end": round(word.end, 2),
                        "probability": round(word.probability, 3),
                    })

        return {
            "language": info.language,
            "language_probability": round(info.language_probability, 3),
            "duration": round(info.duration, 2),
            "full_text": " ".join(full_text_parts),
            "segments": timestamped_lines,
            "words": words,
            "timestamped_transcript": "\n".join(
                f"[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}"
                for seg in timestamped_lines
            ),
        }

    async def transcribe(
        self,
        audio_path: str,
        progress_callback=None,
    ) -> dict:
        """
        Async wrapper around CPU-bound transcription.
        Runs in a thread pool to avoid blocking the event loop.
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Starting transcription: {audio_path}")
        if progress_callback:
            await progress_callback(20, "transcribing")

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._transcribe_sync, audio_path)

        if progress_callback:
            await progress_callback(40, "transcribing")

        word_count = len(result.get("words", []))
        logger.info(
            f"Transcription complete: {result['language']} | "
            f"{result['duration']:.0f}s | {word_count} words"
        )
        return result


transcriber = Transcriber()
