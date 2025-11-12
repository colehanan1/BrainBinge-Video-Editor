"""
HeyGen Social Clipper - Video Processing Pipeline

Transform HeyGen AI videos into viral social media content with:
- Word-level synchronized captions (±50ms accuracy)
- Intelligent B-roll integration from Pexels API
- Brand styling and overlays
- Multi-platform export (Instagram, TikTok, YouTube Shorts)

Architecture:
    7-stage processing pipeline orchestrated by core.orchestrator:
    1. Audio Extraction (modules.audio)
    2. Force Alignment (modules.alignment)
    3. Caption Generation (modules.captions)
    4. Caption Styling (modules.styling)
    5. B-roll Integration (modules.broll)
    6. Video Composition (modules.composition)
    7. Video Encoding (modules.encoding)

Example:
    >>> from src.pipeline import VideoProcessor
    >>> processor = VideoProcessor(config_path="config/brand.yaml")
    >>> result = processor.process_video("input.mp4", "script.txt")
"""

__version__ = "0.1.0-alpha"
__author__ = "BrainBinge"
__license__ = "MIT"

from pathlib import Path

# Package root directory
PACKAGE_ROOT = Path(__file__).parent
PROJECT_ROOT = PACKAGE_ROOT.parent

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "PACKAGE_ROOT",
    "PROJECT_ROOT",
]
