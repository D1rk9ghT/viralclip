"""
Gemini AI service — production-grade with async calls,
structured output, retry logic, and modular analysis functions.
"""

import google.generativeai as genai
import json
import asyncio
from typing import Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import get_settings
from app.ai.prompts import (
    SYSTEM_INSTRUCTION,
    ANALYZE_TRANSCRIPT_PROMPT,
    GENERATE_TITLES_PROMPT,
    RANK_CLIPS_PROMPT,
)

settings = get_settings()


class GeminiService:
    """Production Gemini AI service with async support and retry logic."""

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set — AI features will be unavailable")
            self._available = False
            return

        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            settings.GEMINI_MODEL,
            system_instruction=SYSTEM_INSTRUCTION,
            generation_config=genai.GenerationConfig(
                temperature=0.4,
                top_p=0.9,
                response_mime_type="application/json",
            ),
        )
        self._available = True
        logger.info(f"Gemini service initialized with model: {settings.GEMINI_MODEL}")

    @property
    def is_available(self) -> bool:
        return self._available

    def _parse_json_response(self, text: str) -> list | dict:
        """Safely parse JSON from Gemini response, handling markdown fences."""
        cleaned = text.strip()
        # Strip markdown code fences if present
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first and last lines (``` markers)
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()

        return json.loads(cleaned)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
        retry=retry_if_exception_type((json.JSONDecodeError, Exception)),
        reraise=True,
    )
    async def _generate(self, prompt: str) -> list | dict:
        """
        Core generation method with retry logic.
        Runs the synchronous SDK call in a thread pool to avoid blocking.
        """
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.model.generate_content(prompt)
        )
        return self._parse_json_response(response.text)

    async def analyze_transcript(
        self, transcript: str, max_clips: int = 10
    ) -> list[dict]:
        """
        Analyze a timestamped transcript and identify viral-worthy segments.

        Returns a list of clip candidates with timestamps, titles, hooks,
        viral scores, and categorization.
        """
        if not self._available:
            logger.error("Gemini service unavailable — skipping analysis")
            return []

        prompt = ANALYZE_TRANSCRIPT_PROMPT.format(
            transcript=transcript[:30000],  # Token budget: ~30k chars
            max_clips=max_clips,
        )

        try:
            clips = await self._generate(prompt)
            if not isinstance(clips, list):
                logger.warning("Gemini returned non-list for clip analysis")
                return []

            # Validate and sanitize each clip
            validated = []
            for clip in clips:
                try:
                    validated.append({
                        "start_time": float(clip.get("start_time", 0)),
                        "end_time": float(clip.get("end_time", 0)),
                        "title": str(clip.get("title", "Untitled Clip"))[:200],
                        "hook": str(clip.get("hook", ""))[:500],
                        "viral_score": max(1, min(100, int(clip.get("viral_score", 50)))),
                        "viral_reason": str(clip.get("viral_reason", ""))[:500],
                        "category": str(clip.get("category", "educational")),
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid clip data: {e}")
                    continue

            # Sort by viral score descending
            validated.sort(key=lambda c: c["viral_score"], reverse=True)
            logger.info(f"Gemini identified {len(validated)} viral clips")
            return validated

        except Exception as e:
            logger.error(f"Transcript analysis failed after retries: {e}")
            return []

    async def generate_titles(self, clip_text: str) -> list[str]:
        """Generate alternative viral titles for a clip."""
        if not self._available:
            return []

        prompt = GENERATE_TITLES_PROMPT.format(clip_text=clip_text[:5000])

        try:
            titles = await self._generate(prompt)
            return [str(t)[:200] for t in titles if isinstance(t, str)]
        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            return []

    async def rank_clips(self, clips: list[dict]) -> list[int]:
        """Re-rank clips by viral potential. Returns ordered indices."""
        if not self._available:
            return list(range(len(clips)))

        prompt = RANK_CLIPS_PROMPT.format(clips_json=json.dumps(clips[:20]))

        try:
            ranking = await self._generate(prompt)
            return [int(i) for i in ranking if isinstance(i, (int, float))]
        except Exception as e:
            logger.error(f"Clip ranking failed: {e}")
            return list(range(len(clips)))


# Module-level singleton
gemini_service = GeminiService()
