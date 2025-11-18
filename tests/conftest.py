"""
Pytest Configuration and Shared Fixtures

Provides common fixtures and configuration for all tests.
"""

import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from src.config import Config


# Mock forcealign module if not installed
if 'forcealign' not in sys.modules:
    mock_forcealign = MagicMock()
    # Set up the module structure
    mock_forcealign.ForceAlign = MagicMock
    sys.modules['forcealign'] = mock_forcealign


@pytest.fixture
def test_data_dir() -> Path:
    """
    Provide path to test data directory.

    Returns:
        Path to data/input directory with test files
    """
    return Path(__file__).parent.parent / "data" / "input"


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """
    Provide temporary directory for test outputs.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to temporary output directory
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """
    Provide sample configuration dictionary for testing.

    Returns:
        Dict with minimal valid configuration
    """
    return {
        "version": "1.0",
        "brand": {
            "name": "TestBrand",
            "colors": {
                "primary": "#FF0000",
                "secondary": "#00FF00",
            }
        },
        "captions": {
            "enabled": True,
            "font": {
                "family": "Arial",
                "size": 48,
                "weight": "bold",
            },
            "style": {
                "color": "#FFFFFF",
                "background_color": "#000000",
                "background_opacity": 0.7,
            },
            "animation": {
                "type": "word_highlight",
                "duration": 0.2,
            },
        },
        "broll": {
            "enabled": False,
            "sources": [],
            "settings": {},
        },
        "audio": {
            "music": {
                "enabled": False,
            },
            "processing": {
                "normalize": True,
            },
        },
        "export": {
            "platforms": {
                "instagram": {
                    "enabled": True,
                    "resolution": [1080, 1920],
                    "fps": 30,
                    "bitrate": "10M",
                    "codec": "h264",
                    "profile": "high",
                }
            },
            "naming": {
                "template": "{brand}_{timestamp}_{platform}"
            },
            "metadata": {
                "generate": True,
            },
        },
    }


@pytest.fixture
def config_instance(sample_config: Dict[str, Any]) -> Config:
    """
    Provide Config instance for testing.

    Args:
        sample_config: Sample configuration dictionary

    Returns:
        Validated Config object
    """
    return Config(**sample_config)


@pytest.fixture
def sample_video_path(test_data_dir: Path) -> Path:
    """
    Provide path to sample video file.

    Returns:
        Path to sample video (may not exist yet)
    """
    return test_data_dir / "sample_video.mp4"


@pytest.fixture
def sample_script_path(test_data_dir: Path) -> Path:
    """
    Provide path to sample script file.

    Returns:
        Path to sample script (may not exist yet)
    """
    return test_data_dir / "sample_script.txt"
