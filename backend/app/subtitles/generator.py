"""
ASS subtitle generator with word-level synchronization.
Produces TikTok-style animated captions.
"""

import os
from pathlib import Path
from loguru import logger


# ASS header template for TikTok-style captions
ASS_HEADER = """[Script Info]
Title: ViralClips AI Subtitles
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,72,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,40,40,120,1
Style: Highlight,Arial Black,78,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,40,40,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _format_ass_time(seconds: float) -> str:
    """Convert seconds to ASS timestamp format (H:MM:SS.CC)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"


def generate_word_subtitles(
    words: list[dict],
    clip_start: float = 0,
    clip_end: float = None,
    max_words_per_line: int = 4,
    style: str = "Default",
) -> str:
    """
    Generate ASS subtitles with word-level timing.

    Args:
        words: List of {word, start, end} from Whisper transcription
        clip_start: Start time offset of the clip
        clip_end: End time of the clip
        max_words_per_line: Words per subtitle line
        style: ASS style name

    Returns:
        Complete ASS subtitle file content as string
    """
    # Filter words within clip range
    if clip_end is not None:
        words = [w for w in words if w["start"] >= clip_start and w["end"] <= clip_end]

    if not words:
        return ASS_HEADER + "Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,No captions available\n"

    lines = []
    ass_content = ASS_HEADER

    # Group words into lines
    current_group = []
    for word in words:
        current_group.append(word)
        if len(current_group) >= max_words_per_line:
            lines.append(current_group)
            current_group = []
    if current_group:
        lines.append(current_group)

    # Generate ASS dialogue events
    for line_words in lines:
        line_start = line_words[0]["start"] - clip_start
        line_end = line_words[-1]["end"] - clip_start

        # Ensure non-negative timestamps
        line_start = max(0, line_start)
        line_end = max(line_start + 0.1, line_end)

        start_ts = _format_ass_time(line_start)
        end_ts = _format_ass_time(line_end)

        # Build text with word-by-word highlighting
        text_parts = []
        for w in line_words:
            text_parts.append(w["word"].upper())

        line_text = " ".join(text_parts)

        ass_content += (
            f"Dialogue: 0,{start_ts},{end_ts},{style},,0,0,0,,{line_text}\n"
        )

    logger.info(f"Generated {len(lines)} subtitle lines")
    return ass_content


def save_subtitles(
    ass_content: str,
    output_path: str,
) -> str:
    """Save ASS content to file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_content)
    logger.info(f"Subtitles saved: {output_path}")
    return output_path


def generate_clip_subtitles(
    words: list[dict],
    clip_start: float,
    clip_end: float,
    output_path: str,
    **kwargs,
) -> str:
    """
    Convenience function: generate and save subtitles for a specific clip.
    """
    ass = generate_word_subtitles(
        words=words,
        clip_start=clip_start,
        clip_end=clip_end,
        **kwargs,
    )
    return save_subtitles(ass, output_path)
