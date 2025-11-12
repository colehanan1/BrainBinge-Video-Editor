"""
Core Pipeline Components

Provides base classes and orchestration logic for the video processing pipeline.

Modules:
    orchestrator - Pipeline orchestration and stage coordination
    processor - Base processor interface for all stages
"""

from src.core.processor import BaseProcessor

__all__ = ["BaseProcessor"]
