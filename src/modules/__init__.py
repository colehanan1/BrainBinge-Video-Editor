"""
Processing Stage Modules

Individual processors for each of the 7 pipeline stages.

Modules:
    audio - Audio extraction from video
    alignment - Force alignment of script with audio
    captions - Caption generation with word-level timing
    styling - Caption styling and brand application
    broll - B-roll integration from Pexels API
    composition - Video composition and layering
    encoding - Platform-specific video encoding
"""

__all__ = [
    "AudioExtractor",
    "ForceAligner",
    "CaptionGenerator",
    "CaptionStyler",
    "BRollIntegrator",
    "VideoCompositor",
    "VideoEncoder",
]
