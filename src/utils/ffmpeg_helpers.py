"""
FFmpeg Helper Utilities

Common filter graph builders and utilities for video composition.

Provides reusable functions for:
- Video scaling and padding
- Fade transitions (in/out)
- Text overlays
- Audio processing
- Path escaping for filters

Example:
    >>> from src.utils.ffmpeg_helpers import escape_filter_path, build_fade
    >>> escaped = escape_filter_path("/path/to/file.ass")
    >>> fade_in = build_fade(stream, "in", start=0, duration=0.5)
"""

import platform
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import ffmpeg


def escape_filter_path(path: Path) -> str:
    """
    Escape file path for FFmpeg filter usage.

    FFmpeg filters (especially subtitles) require special path escaping:
    - Windows: Escape backslashes and colons
    - Unix: Escape colons

    Args:
        path: Path to escape

    Returns:
        Escaped path string safe for FFmpeg filters

    Example:
        >>> escape_filter_path(Path("C:\\Videos\\captions.ass"))
        'C\\:\\\\Videos\\\\captions.ass'
        >>> escape_filter_path(Path("/home/user/captions.ass"))
        '/home/user/captions.ass'
    """
    path_str = str(path)

    if platform.system() == "Windows":
        # Windows paths need both backslash and colon escaping
        path_str = path_str.replace('\\', '\\\\').replace(':', '\\:')
    else:
        # Unix paths just need colon escaping
        path_str = path_str.replace(':', '\\:')

    return path_str


def build_scale_filter(
    stream: ffmpeg.Stream,
    width: int,
    height: int,
    keep_aspect: bool = False,
) -> ffmpeg.Stream:
    """
    Add scale filter to stream.

    Args:
        stream: Input video stream
        width: Target width in pixels
        height: Target height in pixels
        keep_aspect: If True, maintains aspect ratio with padding

    Returns:
        Scaled video stream

    Example:
        >>> video = ffmpeg.input('video.mp4')
        >>> scaled = build_scale_filter(video, 1280, 720)
    """
    if keep_aspect:
        # Scale to fit within dimensions, maintaining aspect ratio
        return stream.filter('scale', f'{width}:{height}:force_original_aspect_ratio=decrease')
    else:
        # Scale to exact dimensions
        return stream.filter('scale', width, height)


def build_fade(
    stream: ffmpeg.Stream,
    fade_type: str,
    start_time: float = 0,
    duration: float = 0.5,
) -> ffmpeg.Stream:
    """
    Add fade transition to stream.

    Args:
        stream: Input stream (video or audio)
        fade_type: "in" or "out"
        start_time: When to start fade (seconds)
        duration: Fade duration (seconds)

    Returns:
        Stream with fade applied

    Example:
        >>> video = ffmpeg.input('video.mp4')
        >>> faded = build_fade(video, "in", start_time=0, duration=0.5)
    """
    if fade_type not in ['in', 'out']:
        raise ValueError(f"fade_type must be 'in' or 'out', got: {fade_type}")

    return stream.filter(
        'fade',
        type=fade_type,
        start_time=start_time,
        duration=duration,
    )


def build_text_overlay(
    stream: ffmpeg.Stream,
    text: str,
    fontsize: int = 48,
    fontcolor: str = 'white',
    x: str = '(w-text_w)/2',  # Centered
    y: str = '50',  # 50px from top
    box: bool = True,
    boxcolor: str = 'black@0.6',
    boxborderw: int = 10,
) -> ffmpeg.Stream:
    """
    Add text overlay using drawtext filter.

    Args:
        stream: Input video stream
        text: Text to display
        fontsize: Font size in pixels
        fontcolor: Font color (name or hex)
        x: X position expression (default: centered)
        y: Y position expression (default: 50px from top)
        box: Enable background box
        boxcolor: Box color with alpha (e.g., 'black@0.6' = 60% opaque)
        boxborderw: Box border width in pixels

    Returns:
        Stream with text overlay

    Example:
        >>> video = ffmpeg.input('video.mp4')
        >>> overlaid = build_text_overlay(video, "My Video Title")
    """
    params = {
        'text': text,
        'fontsize': fontsize,
        'fontcolor': fontcolor,
        'x': x,
        'y': y,
    }

    if box:
        params.update({
            'box': 1,
            'boxcolor': boxcolor,
            'boxborderw': boxborderw,
        })

    return stream.drawtext(**params)


def build_pip_overlay(
    main_stream: ffmpeg.Stream,
    pip_stream: ffmpeg.Stream,
    x: str = 'main_w-overlay_w-10',
    y: str = 'main_h-overlay_h-10',
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
) -> ffmpeg.Stream:
    """
    Add picture-in-picture overlay.

    Args:
        main_stream: Main video stream
        pip_stream: PIP video stream (already scaled)
        x: X position expression (default: bottom-right, 10px padding)
        y: Y position expression (default: bottom-right, 10px padding)
        start_time: When to show PIP (seconds)
        end_time: When to hide PIP (seconds)

    Returns:
        Main stream with PIP overlaid

    Example:
        >>> main = ffmpeg.input('main.mp4')
        >>> pip = ffmpeg.input('pip.mp4').filter('scale', 400, 300)
        >>> composed = build_pip_overlay(main, pip, start_time=5, end_time=15)
    """
    params = {'x': x, 'y': y}

    # Add time-based enable condition
    if start_time is not None and end_time is not None:
        params['enable'] = f'between(t,{start_time},{end_time})'

    return main_stream.overlay(pip_stream, **params)


def build_audio_ducking(
    audio_stream: ffmpeg.Stream,
    intervals: List[Tuple[float, float]],
    ducking_volume: float = 0.5,
) -> ffmpeg.Stream:
    """
    Apply audio ducking (volume reduction) during intervals.

    Args:
        audio_stream: Input audio stream
        intervals: List of (start, end) time tuples in seconds
        ducking_volume: Volume multiplier during intervals (0.0-1.0)

    Returns:
        Audio stream with ducking applied

    Example:
        >>> audio = ffmpeg.input('video.mp4').audio
        >>> ducked = build_audio_ducking(audio, [(5, 10), (20, 25)], 0.5)
    """
    if not intervals:
        return audio_stream

    if not 0.0 <= ducking_volume <= 1.0:
        raise ValueError(f"ducking_volume must be 0.0-1.0, got: {ducking_volume}")

    # Build conditional volume expression
    # Example: "if(between(t,5,10),0.5,1.0)*if(between(t,20,25),0.5,1.0)"
    conditions = '*'.join([
        f"if(between(t,{start},{end}),{ducking_volume},1.0)"
        for start, end in intervals
    ])

    return audio_stream.filter('volume', conditions)


def build_crossfade_transition(
    stream1: ffmpeg.Stream,
    stream2: ffmpeg.Stream,
    transition_time: float,
    duration: float = 1.0,
) -> ffmpeg.Stream:
    """
    Build crossfade transition between two video streams.

    Args:
        stream1: First video stream
        stream2: Second video stream
        transition_time: When to start transition (seconds)
        duration: Crossfade duration (seconds)

    Returns:
        Blended video stream

    Example:
        >>> clip1 = ffmpeg.input('clip1.mp4')
        >>> clip2 = ffmpeg.input('clip2.mp4')
        >>> faded = build_crossfade_transition(clip1, clip2, 10, 1.0)
    """
    # Offset second stream to start at transition time
    stream2_offset = stream2.filter('setpts', f'PTS+{transition_time}/TB')

    # Apply crossfade using blend filter
    return stream1.filter(
        'blend',
        stream2_offset,
        all_mode='normal',
        all_opacity=f'if(gte(T,{transition_time}),if(lte(T,{transition_time + duration}),(T-{transition_time})/{duration},1),0)',
    )


def probe_video_info(video_path: Path) -> Dict[str, Any]:
    """
    Extract video information using ffprobe.

    Args:
        video_path: Path to video file

    Returns:
        Dict with video metadata:
            - duration: Video duration in seconds
            - width: Video width in pixels
            - height: Video height in pixels
            - fps: Frames per second
            - codec: Video codec name
            - bitrate: Video bitrate in bps

    Example:
        >>> info = probe_video_info(Path("video.mp4"))
        >>> print(f"Duration: {info['duration']}s, Resolution: {info['width']}x{info['height']}")
    """
    probe = ffmpeg.probe(str(video_path))

    # Find video stream
    video_stream = next(
        (stream for stream in probe['streams'] if stream['codec_type'] == 'video'),
        None
    )

    if not video_stream:
        raise ValueError(f"No video stream found in {video_path}")

    # Extract metadata
    return {
        'duration': float(probe['format']['duration']),
        'width': int(video_stream['width']),
        'height': int(video_stream['height']),
        'fps': eval(video_stream['r_frame_rate']),  # Evaluate fraction like "30/1"
        'codec': video_stream['codec_name'],
        'bitrate': int(probe['format'].get('bit_rate', 0)),
    }


def validate_ffmpeg_installed() -> bool:
    """
    Check if FFmpeg is installed and accessible.

    Returns:
        True if FFmpeg is installed, False otherwise

    Example:
        >>> if not validate_ffmpeg_installed():
        ...     print("Please install FFmpeg")
    """
    try:
        ffmpeg.probe('test')
        return True
    except (ffmpeg.Error, FileNotFoundError):
        return False
