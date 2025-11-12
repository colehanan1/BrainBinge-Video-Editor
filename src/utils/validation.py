"""
Input Validation Utilities

Helper functions for validating video, audio, script, and config files.
"""

from pathlib import Path
from typing import List


def validate_video(video_path: Path) -> List[str]:
    """Validate video file format, codec, resolution."""
    # TODO: Check file exists
    # TODO: Probe video with FFmpeg
    # TODO: Validate codec, resolution, fps
    raise NotImplementedError()


def validate_script(script_path: Path) -> List[str]:
    """Validate script file format and content."""
    # TODO: Check file exists
    # TODO: Validate format (TXT/JSON/CSV)
    # TODO: Check content is not empty
    raise NotImplementedError()


def validate_audio(audio_path: Path) -> List[str]:
    """Validate audio file format."""
    # TODO: Check file exists
    # TODO: Validate WAV format
    # TODO: Check sample rate (16kHz mono)
    raise NotImplementedError()
