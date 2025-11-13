"""
Stage 4: Caption Styling

Applies viral-worthy styling to captions using ASS (Advanced SubStation Alpha) format.

Converts plain SRT captions into visually stunning ASS captions optimized for
TikTok/Instagram Reels with:
- White text with black outline (readable on any background)
- Blur effect for modern aesthetic
- Optimal font sizing for mobile viewing (24-28pt)
- Bottom-center positioning
- BGR color format (ASS standard)

Key Features:
    - ASS format with advanced styling
    - White text + black outline + blur effect
    - Mobile-optimized typography
    - Configurable colors and positioning
    - 1280×720 video optimization

Example:
    >>> from src.modules.styling import CaptionStyler
    >>> styler = CaptionStyler(config)
    >>> result = styler.process("captions.srt", "styled.ass")
"""

import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import Config
from src.core.processor import BaseProcessor, ProcessorResult

logger = logging.getLogger(__name__)


class StylingError(Exception):
    """Raised when caption styling fails."""
    pass


class CaptionStyler(BaseProcessor):
    """
    Apply viral-worthy styling to captions using ASS format.

    Converts plain SRT captions to visually enhanced ASS format with:
    - Bold white text with black outline
    - Blur effect (\be1) for modern aesthetic
    - Optimal positioning for social media
    - Mobile-friendly font sizing

    ASS Style Format:
        Style: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour,
               OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut,
               ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow,
               Alignment, MarginL, MarginR, MarginV, Encoding

    Args:
        config: Configuration object
        temp_dir: Directory for temporary files
    """

    def __init__(self, config: Config, temp_dir: Optional[Path] = None):
        super().__init__(config, temp_dir)

        # Get caption styling from config
        caption_config = getattr(config, "captions", {})
        font_config = getattr(caption_config, "font", None)
        style_config = getattr(caption_config, "style", None)

        # Font settings
        if font_config:
            self.font_family = getattr(font_config, "family", "Arial")
            self.font_size = getattr(font_config, "size", 28)
            self.font_weight = getattr(font_config, "weight", "bold")
        else:
            self.font_family = "Arial"
            self.font_size = 28
            self.font_weight = "bold"

        # Style settings
        if style_config:
            text_color = getattr(style_config, "color", "#FFFFFF")
            self.text_color = text_color if text_color is not None else "#FFFFFF"

            outline_color = getattr(style_config, "stroke_color", "#000000")
            self.outline_color = outline_color if outline_color is not None else "#000000"

            outline_width = getattr(style_config, "stroke_width", 3)
            self.outline_width = outline_width if outline_width is not None else 3
        else:
            self.text_color = "#FFFFFF"
            self.outline_color = "#000000"
            self.outline_width = 3

        # Video dimensions (standard for social media)
        self.video_width = 1280
        self.video_height = 720

    def process(
        self,
        input_path: Path,
        output_path: Path,
        **kwargs: Any,
    ) -> ProcessorResult:
        """
        Apply ASS styling to SRT captions.

        Args:
            input_path: Path to SRT caption file
            output_path: Path for styled ASS output
            **kwargs: Additional parameters
                - video_width: Video width in pixels (default: 1280)
                - video_height: Video height in pixels (default: 720)
                - font_size: Font size override (default: from config)

        Returns:
            ProcessorResult with styled ASS file and metadata

        Raises:
            StylingError: If styling fails
        """
        start_time = time.time()
        video_width = kwargs.get("video_width", self.video_width)
        video_height = kwargs.get("video_height", self.video_height)
        font_size = kwargs.get("font_size", self.font_size)

        logger.info(f"Starting caption styling: {input_path.name}")
        logger.info(f"Video resolution: {video_width}×{video_height}")
        logger.info(f"Font: {self.font_family} {font_size}pt")

        try:
            # Parse SRT file
            logger.info(f"Parsing SRT file: {input_path}")
            captions = self._parse_srt(input_path)
            logger.info(f"Loaded {len(captions)} captions")

            if not captions:
                raise StylingError("No captions found in SRT file")

            # Generate ASS file
            logger.info(f"Generating ASS file: {output_path}")
            self._write_ass(
                captions,
                output_path,
                video_width=video_width,
                video_height=video_height,
                font_size=font_size,
            )

            processing_time = time.time() - start_time
            logger.info(f"Styling completed in {processing_time:.2f}s")

            return ProcessorResult(
                success=True,
                output_path=output_path,
                metadata={
                    "caption_count": len(captions),
                    "video_resolution": f"{video_width}×{video_height}",
                    "font": f"{self.font_family} {font_size}pt",
                    "processing_time": round(processing_time, 2),
                },
            )

        except StylingError:
            raise
        except Exception as e:
            logger.error(f"Caption styling failed: {e}")
            raise StylingError(f"Caption styling failed: {e}")

    def _parse_srt(self, srt_path: Path) -> List[Dict[str, Any]]:
        """
        Parse SRT file into list of caption dicts.

        Args:
            srt_path: Path to SRT file

        Returns:
            List of caption dicts with start, end, text
        """
        captions = []

        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split by blank lines
        blocks = re.split(r'\n\n+', content.strip())

        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue

            # Line 0: Caption number (skip)
            # Line 1: Timestamp
            # Line 2+: Caption text

            timestamp_line = lines[1]
            text = '\n'.join(lines[2:])

            # Parse timestamp: 00:00:00,000 --> 00:00:01,000
            match = re.match(
                r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})',
                timestamp_line
            )

            if match:
                start_h, start_m, start_s, start_ms = match.groups()[:4]
                end_h, end_m, end_s, end_ms = match.groups()[4:]

                start_seconds = (
                    int(start_h) * 3600 +
                    int(start_m) * 60 +
                    int(start_s) +
                    int(start_ms) / 1000.0
                )

                end_seconds = (
                    int(end_h) * 3600 +
                    int(end_m) * 60 +
                    int(end_s) +
                    int(end_ms) / 1000.0
                )

                captions.append({
                    "start": start_seconds,
                    "end": end_seconds,
                    "text": text,
                })

        return captions

    def _write_ass(
        self,
        captions: List[Dict[str, Any]],
        output_path: Path,
        video_width: int,
        video_height: int,
        font_size: int,
    ) -> None:
        """
        Write captions to ASS file with viral styling.

        ASS format includes:
        - [Script Info]: Video metadata
        - [V4+ Styles]: Style definitions
        - [Events]: Timed captions with styling

        Args:
            captions: List of caption dicts
            output_path: Path to write ASS file
            video_width: Video width in pixels
            video_height: Video height in pixels
            font_size: Font size in points
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert hex colors to BGR format (ASS standard)
        primary_color = self._hex_to_ass_color(self.text_color)
        outline_color = self._hex_to_ass_color(self.outline_color)

        # Determine bold flag
        bold = -1 if self.font_weight == "bold" else 0

        with open(output_path, "w", encoding="utf-8") as f:
            # [Script Info] section
            f.write("[Script Info]\n")
            f.write(f"; Generated by BrainBinge Video Editor\n")
            f.write(f"Title: Styled Captions\n")
            f.write(f"ScriptType: v4.00+\n")
            f.write(f"PlayResX: {video_width}\n")
            f.write(f"PlayResY: {video_height}\n")
            f.write(f"WrapStyle: 0\n")
            f.write(f"ScaledBorderAndShadow: yes\n")
            f.write(f"\n")

            # [V4+ Styles] section
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")

            # Default style with viral settings
            f.write(
                f"Style: Default,{self.font_family},{font_size},"
                f"{primary_color},{primary_color},{outline_color},&H00000000,"  # PrimaryColour, SecondaryColour, OutlineColour, BackColour
                f"{bold},0,0,0,"  # Bold, Italic, Underline, StrikeOut
                f"100,100,0,0,"  # ScaleX, ScaleY, Spacing, Angle
                f"1,{self.outline_width},0,"  # BorderStyle, Outline, Shadow
                f"2,10,10,20,1\n"  # Alignment (2=bottom-center), MarginL, MarginR, MarginV, Encoding
            )
            f.write("\n")

            # [Events] section
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

            # Write each caption as dialogue line
            for caption in captions:
                start_time = self._format_ass_time(caption["start"])
                end_time = self._format_ass_time(caption["end"])
                text = caption["text"].replace("\n", "\\N")  # ASS line break

                # Add blur effect (\be1) for modern aesthetic
                styled_text = f"{{\\be1}}{text}"

                f.write(
                    f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{styled_text}\n"
                )

        logger.info(f"ASS file saved: {output_path}")

    def _hex_to_ass_color(self, hex_color: str) -> str:
        """
        Convert hex color (#RRGGBB) to ASS BGR format (&H00BBGGRR).

        ASS uses BGR (Blue-Green-Red) instead of RGB, with alpha channel.

        Args:
            hex_color: Hex color string (#RRGGBB or #RGB)

        Returns:
            ASS color string (&H00BBGGRR)
        """
        # Safety check for None values
        if hex_color is None:
            hex_color = "#FFFFFF"  # Default to white

        # Remove # prefix
        hex_color = hex_color.lstrip('#')

        # Expand short form (#RGB → #RRGGBB)
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])

        # Parse RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Convert to BGR with alpha channel (00 = fully opaque)
        return f"&H00{b:02X}{g:02X}{r:02X}"

    def _format_ass_time(self, seconds: float) -> str:
        """
        Format time in seconds to ASS format: H:MM:SS.cc

        ASS uses centiseconds (hundredths of a second) instead of milliseconds.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted ASS timestamp
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds % 1) * 100)

        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

    def validate(self, input_path: Path, **kwargs: Any) -> List[str]:
        """
        Validate SRT caption file before styling.

        Args:
            input_path: Path to SRT file
            **kwargs: Additional parameters

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check file exists
        if not input_path.exists():
            errors.append(f"Caption file not found: {input_path}")
            return errors

        # Check file is not empty
        if input_path.stat().st_size == 0:
            errors.append("Caption file is empty")
            return errors

        # Validate SRT format
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for timestamp pattern
            if not re.search(r'\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}', content):
                errors.append("Invalid SRT format: no timestamps found")

            # Check for caption text
            blocks = re.split(r'\n\n+', content.strip())
            if len(blocks) == 0:
                errors.append("No captions found in SRT file")

        except Exception as e:
            errors.append(f"Failed to validate SRT file: {e}")

        return errors

    def estimate_duration(self, input_path: Path, **kwargs: Any) -> float:
        """
        Estimate styling duration.

        Styling is extremely fast (parsing + writing text file).

        Args:
            input_path: Path to caption file
            **kwargs: Additional parameters

        Returns:
            Estimated time in seconds
        """
        return 0.5  # Styling is very fast
