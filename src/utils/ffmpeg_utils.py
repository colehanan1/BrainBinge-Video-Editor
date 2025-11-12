"""
FFmpeg Utility Functions

Wrappers for common FFmpeg operations using ffmpeg-python library.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional


def run_ffmpeg(command: List[str], **kwargs: Any) -> None:
    """Execute FFmpeg command."""
    # TODO: Run FFmpeg with error handling
    raise NotImplementedError()


def probe_video(video_path: Path) -> Dict[str, Any]:
    """Get video metadata using ffprobe."""
    # TODO: Run ffprobe
    # TODO: Parse JSON output
    # TODO: Return metadata dict
    raise NotImplementedError()


def extract_audio(video_path: Path, output_path: Path, sample_rate: int = 16000) -> None:
    """Extract audio from video."""
    # TODO: Use ffmpeg-python to extract audio
    # TODO: Convert to specified sample rate
    # TODO: Convert to mono
    raise NotImplementedError()


def get_video_duration(video_path: Path) -> float:
    """Get video duration in seconds."""
    # TODO: Probe video
    # TODO: Extract duration
    raise NotImplementedError()
