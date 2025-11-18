"""
Configuration Management for HeyGen Social Clipper

Loads and validates brand configuration from YAML/JSON files.
Provides type-safe access to configuration values using Pydantic models.

Configuration Structure:
    - brand: Brand identity (name, logo, colors)
    - captions: Caption styling (font, colors, animations)
    - broll: B-roll integration settings
    - audio: Audio mixing and music
    - overlays: Logo and watermark positioning
    - export: Platform-specific export settings

Example:
    >>> from src.config import ConfigLoader
    >>> config = ConfigLoader.load("config/brand.yaml")
    >>> print(config.brand.name)
    'BrainBinge'
    >>> print(config.captions.font.size)
    48
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, validator


class FontConfig(BaseModel):
    """Font configuration for captions."""

    family: str = Field(..., description="Font family name")
    weight: str = Field(default="bold", description="Font weight")
    size: int = Field(default=48, ge=12, le=200, description="Font size in pixels")


class CaptionStyleConfig(BaseModel):
    """Caption visual styling configuration."""

    color: str = Field(default="#FFFFFF", description="Text color (hex)")
    background_color: str = Field(
        default="#000000", description="Background color (hex)"
    )
    background_opacity: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Background opacity"
    )
    stroke_color: Optional[str] = Field(
        default=None, description="Text stroke color (hex)"
    )
    stroke_width: int = Field(default=0, ge=0, le=10, description="Stroke width")


class CaptionAnimationConfig(BaseModel):
    """Caption animation configuration."""

    type: str = Field(
        default="word_highlight",
        description="Animation type: none, word_highlight, fade_in, slide_in",
    )
    duration: float = Field(
        default=0.2, ge=0.0, le=2.0, description="Animation duration in seconds"
    )
    highlight_color: Optional[str] = Field(
        default="#F7B801", description="Highlight color for word animations"
    )


class CaptionConfig(BaseModel):
    """Complete caption configuration."""

    enabled: bool = Field(default=True, description="Enable caption generation")
    font: Optional[FontConfig] = Field(default=None, description="Font configuration")
    style: Optional[Union[str, CaptionStyleConfig]] = Field(default="word_highlight", description="Caption style")
    animation: Optional[CaptionAnimationConfig] = Field(default=None, description="Animation configuration")
    position: Union[str, Dict[str, Union[str, int]]] = Field(
        default="bottom",
        description="Position: 'top', 'center', 'bottom' or detailed dict"
    )

    @field_validator('font', mode='before')
    @classmethod
    def set_default_font(cls, v):
        """Provide default font if not specified."""
        if v is None:
            return FontConfig(
                font_family="Montserrat",
                size=60,
                weight="bold",
                color="#FFFFFF"
            )
        return v

    @field_validator('animation', mode='before')
    @classmethod
    def set_default_animation(cls, v):
        """Provide default animation if not specified."""
        if v is None:
            return CaptionAnimationConfig(
                type="word_highlight",
                duration=0.3,
                easing="ease_out"
            )
        return v

    @field_validator('style', mode='before')
    @classmethod
    def convert_style(cls, v):
        """Convert string style to CaptionStyleConfig."""
        if isinstance(v, str):
            # Map simple string to style config
            return CaptionStyleConfig(
                background_enabled=True if v == "word_highlight" else False,
                background_color="#000000" if v == "word_highlight" else None,
                background_opacity=0.8,
                border_enabled=False,
                shadow_enabled=True,
                shadow_color="#000000",
                shadow_blur=5,
                shadow_offset_x=2,
                shadow_offset_y=2
            )
        return v

    @field_validator('position', mode='before')
    @classmethod
    def convert_position(cls, v):
        """Convert string position to dict."""
        if isinstance(v, str):
            positions = {
                "top": {"vertical": "top", "horizontal": "center", "margin_top": 150},
                "center": {"vertical": "center", "horizontal": "center"},
                "bottom": {"vertical": "bottom", "horizontal": "center", "margin_bottom": 150},
            }
            return positions.get(v, positions["bottom"])
        return v


class BRollSourceConfig(BaseModel):
    """B-roll source configuration."""

    type: str = Field(..., description="Source type: pexels, local")
    enabled: bool = Field(default=True, description="Enable this source")
    api_key: Optional[str] = Field(default=None, description="API key (if required)")
    path: Optional[Path] = Field(default=None, description="Local path (if local)")


class BRollConfig(BaseModel):
    """B-roll integration configuration."""

    enabled: bool = Field(default=True, description="Enable B-roll integration")
    sources: List[BRollSourceConfig] = Field(
        default_factory=list, description="B-roll sources"
    )
    settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "min_duration": 2.0,
            "max_duration": 5.0,
            "transition_type": "crossfade",
            "transition_duration": 0.5,
        }
    )
    keywords: Dict[str, List[str]] = Field(
        default_factory=dict, description="Keyword-to-category mapping"
    )


class NoiseReductionConfig(BaseModel):
    """Noise reduction configuration."""
    enabled: bool = Field(default=False, description="Enable noise reduction")
    strength: float = Field(default=0.5, ge=0.0, le=1.0, description="Noise reduction strength")


class AudioConfig(BaseModel):
    """Audio processing configuration."""

    # Extraction settings
    sample_rate: int = Field(default=16000, description="Audio sample rate in Hz (16kHz for Whisper)")
    channels: int = Field(default=1, ge=1, le=2, description="Number of audio channels (1=mono, 2=stereo)")
    format: str = Field(default="wav", description="Audio format")

    # Normalization settings
    normalize: bool = Field(default=True, description="Enable audio normalization")
    target_loudness: int = Field(default=-16, description="Target loudness in LUFS for normalization")

    # Noise reduction
    noise_reduction: NoiseReductionConfig = Field(
        default_factory=NoiseReductionConfig,
        description="Noise reduction settings"
    )

    # Music settings (legacy)
    music: Dict[str, Any] = Field(
        default_factory=lambda: {
            "enabled": True,
            "source": "assets/music",
            "volume": 0.15,
            "fade_in": 1.0,
            "fade_out": 1.0,
        }
    )
    processing: Dict[str, Any] = Field(
        default_factory=lambda: {
            "normalize": True,
            "compression": True,
            "voice_volume": 1.0,
        }
    )


class PlatformExportConfig(BaseModel):
    """Platform-specific export settings."""

    enabled: bool = Field(default=True)
    resolution: List[int] = Field(default=[1080, 1920])
    fps: int = Field(default=30, ge=24, le=60)
    bitrate: str = Field(default="10M")
    codec: str = Field(default="h264")
    profile: str = Field(default="high")


class ExportConfig(BaseModel):
    """Export configuration for all platforms."""

    platforms: Dict[str, PlatformExportConfig] = Field(default_factory=dict)
    naming: Dict[str, str] = Field(
        default_factory=lambda: {"template": "{brand}_{timestamp}_{platform}"}
    )
    metadata: Dict[str, bool] = Field(
        default_factory=lambda: {
            "generate": True,
            "include_hashtags": True,
            "include_description": True,
        }
    )


class BrandConfig(BaseModel):
    """Brand identity configuration."""

    name: str = Field(..., description="Brand name")
    logo: Optional[Path] = Field(default=None, description="Logo file path")
    watermark: Optional[Path] = Field(default=None, description="Watermark file path")
    colors: Dict[str, str] = Field(default_factory=dict, description="Brand colors")


class Config(BaseModel):
    """
    Complete configuration for HeyGen Social Clipper.

    This is the root configuration model that contains all settings
    for the video processing pipeline.
    """

    version: str = Field(default="1.0", description="Config file version")
    brand: BrandConfig
    captions: CaptionConfig
    broll: BRollConfig
    audio: AudioConfig
    export: ExportConfig

    class Config:
        """Pydantic configuration."""

        extra = "allow"  # Allow additional fields
        validate_assignment = True


class ConfigLoader:
    """
    Configuration file loader with validation.

    Loads YAML or JSON configuration files and validates them against
    the Config schema using Pydantic.

    Example:
        >>> config = ConfigLoader.load("config/brand.yaml")
        >>> config = ConfigLoader.load_dict(config_dict)
    """

    @staticmethod
    def load(config_path: Union[str, Path]) -> Config:
        """
        Load configuration from file.

        Args:
            config_path: Path to YAML or JSON configuration file

        Returns:
            Validated Config object

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config validation fails
        """
        import json
        import yaml
        from pathlib import Path

        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        # Load file based on extension
        with open(path, 'r') as f:
            if path.suffix in ['.yaml', '.yml']:
                config_dict = yaml.safe_load(f)
            elif path.suffix == '.json':
                config_dict = json.load(f)
            else:
                raise ValueError(f"Unsupported config format: {path.suffix}. Use .yaml, .yml, or .json")

        if not config_dict:
            raise ValueError(f"Empty configuration file: {path}")

        # Return validated Config object
        return ConfigLoader.load_dict(config_dict)

    @staticmethod
    def load_dict(config_dict: Dict[str, Any]) -> Config:
        """
        Load configuration from dictionary.

        Args:
            config_dict: Configuration as dictionary

        Returns:
            Validated Config object

        Raises:
            ValueError: If config validation fails
        """
        # TODO: Validate dict against Config model
        return Config(**config_dict)

    @staticmethod
    def save(config: Config, output_path: Union[str, Path], format: str = "yaml") -> None:
        """
        Save configuration to file.

        Args:
            config: Config object to save
            output_path: Output file path
            format: Output format ('yaml' or 'json')

        Raises:
            ValueError: If format is invalid
        """
        # TODO: Implement config saving
        # TODO: Pretty-print YAML/JSON
        raise NotImplementedError("Config saving not yet implemented")

    @staticmethod
    def validate_schema(config_dict: Dict[str, Any]) -> List[str]:
        """
        Validate configuration against schema without loading.

        Args:
            config_dict: Configuration dictionary to validate

        Returns:
            List of validation errors (empty if valid)
        """
        # TODO: Implement schema validation
        # TODO: Return detailed error messages
        raise NotImplementedError("Schema validation not yet implemented")
