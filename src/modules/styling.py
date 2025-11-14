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
import platform
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import Config
from src.core.processor import BaseProcessor, ProcessorResult
from src.utils.colors import calculate_contrast_ratio, hex_to_ass_bgr

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

        # Font settings (increased 1.5x: 28pt → 42pt)
        if font_config:
            self.font_family = getattr(font_config, "family", "Arial")
            self.font_size = getattr(font_config, "size", 42)  # TikTok-style larger font
            self.font_weight = getattr(font_config, "weight", "bold")
        else:
            self.font_family = "Arial"
            self.font_size = 42  # Increased from 28 to 42 (1.5x)
            self.font_weight = "bold"

        # Style settings
        if style_config:
            text_color = getattr(style_config, "color", "#FFFFFF")
            self.text_color = text_color if text_color is not None else "#FFFFFF"

            outline_color = getattr(style_config, "stroke_color", "#000000")
            self.outline_color = outline_color if outline_color is not None else "#000000"

            outline_width = getattr(style_config, "stroke_width", 3)
            self.outline_width = outline_width if outline_width is not None else 3

            # TikTok-style word highlighting
            self.enable_word_highlight = getattr(style_config, "word_highlight", True)
            highlight_color = getattr(style_config, "highlight_color", "#FFD700")
            self.highlight_color = highlight_color if highlight_color is not None else "#FFD700"  # Gold
        else:
            self.text_color = "#FFFFFF"
            self.outline_color = "#000000"
            self.outline_width = 3
            self.enable_word_highlight = True
            self.highlight_color = "#FFD700"  # Gold for TikTok-style

        # Video dimensions (standard for social media)
        self.video_width = 1280
        self.video_height = 720

        # Validate font availability
        self._validate_font()

    def process(
        self,
        input_path: Path,
        output_path: Path,
        **kwargs: Any,
    ) -> ProcessorResult:
        """
        Apply ASS styling to SRT captions with TikTok-style word highlighting.

        Args:
            input_path: Path to SRT caption file
            output_path: Path for styled ASS output
            **kwargs: Additional parameters
                - video_width: Video width in pixels (default: 1280)
                - video_height: Video height in pixels (default: 720)
                - font_size: Font size override (default: from config)
                - alignment_json: Path to alignment JSON for word-level highlighting

        Returns:
            ProcessorResult with styled ASS file and metadata

        Raises:
            StylingError: If styling fails
        """
        start_time = time.time()
        video_width = kwargs.get("video_width", self.video_width)
        video_height = kwargs.get("video_height", self.video_height)
        font_size = kwargs.get("font_size", self.font_size)
        alignment_json = kwargs.get("alignment_json", None)

        logger.info(f"Starting caption styling: {input_path.name}")
        logger.info(f"Video resolution: {video_width}×{video_height}")
        logger.info(f"Font: {self.font_family} {font_size}pt")
        if self.enable_word_highlight:
            logger.info(f"Word highlighting: enabled (color: {self.highlight_color})")

        try:
            # Parse SRT file
            logger.info(f"Parsing SRT file: {input_path}")
            captions = self._parse_srt(input_path)
            logger.info(f"Loaded {len(captions)} captions")

            if not captions:
                raise StylingError("No captions found in SRT file")

            # Load word-level timing for highlighting (if available)
            word_timings = None
            if self.enable_word_highlight and alignment_json and Path(alignment_json).exists():
                logger.info(f"Loading word timings from {alignment_json}")
                word_timings = self._load_word_timings(alignment_json)
                logger.info(f"Loaded {len(word_timings)} word timings")

            # Generate ASS file
            logger.info(f"Generating ASS file: {output_path}")
            self._write_ass(
                captions,
                output_path,
                video_width=video_width,
                video_height=video_height,
                font_size=font_size,
                word_timings=word_timings,
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
                    "word_highlight": self.enable_word_highlight,
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

    def _load_word_timings(self, alignment_json: Path) -> List[Dict[str, Any]]:
        """
        Load word-level timings from alignment JSON.

        Args:
            alignment_json: Path to alignment JSON file

        Returns:
            List of word timing dicts with start, end, word
        """
        import json

        try:
            with open(alignment_json, "r", encoding="utf-8") as f:
                data = json.load(f)

            word_timings = []
            if "words" in data:
                for word_data in data["words"]:
                    word_timings.append({
                        "word": word_data.get("word", ""),
                        "start": word_data.get("start", 0.0),
                        "end": word_data.get("end", 0.0),
                    })

            return word_timings

        except Exception as e:
            logger.warning(f"Failed to load word timings: {e}")
            return []

    def _write_highlighted_captions(
        self,
        file_handle,
        captions: List[Dict[str, Any]],
        word_timings: List[Dict[str, Any]],
    ) -> None:
        """
        Write captions with TikTok-style word-by-word highlighting.

        For each caption, generates dialogue events where words progressively
        change color as they're spoken (like TikTok/Instagram Reels).

        Args:
            file_handle: Open file handle for ASS file
            captions: List of caption dicts with start, end, text
            word_timings: List of word timing dicts with word, start, end
        """
        # Convert highlight color to ASS BGR format
        highlight_color_ass = self._hex_to_ass_color(self.highlight_color)
        default_color_ass = self._hex_to_ass_color(self.text_color)

        # Build word index for quick lookup
        word_index = 0

        for caption in captions:
            caption_start = caption["start"]
            caption_end = caption["end"]
            caption_text = caption["text"]

            # Split caption into words (preserve punctuation)
            caption_words = caption_text.split()

            if not caption_words:
                continue

            # Find words that overlap with this caption timespan
            words_in_caption = []
            for i in range(word_index, len(word_timings)):
                word_data = word_timings[i]
                word_start = word_data["start"]
                word_end = word_data["end"]

                # Check if word overlaps with caption timespan
                if word_end < caption_start:
                    continue
                if word_start > caption_end:
                    break

                words_in_caption.append(word_data)

            # Update word index for next caption
            if words_in_caption:
                word_index += len(words_in_caption)

            # Generate dialogue events with word highlighting
            # Strategy: Create events for each word transition
            if words_in_caption and len(words_in_caption) >= len(caption_words) * 0.7:
                # We have good word timing coverage - use word-by-word highlighting
                for i, word_timing in enumerate(words_in_caption):
                    word_start = word_timing["start"]
                    word_end = word_timing["end"]

                    # Build styled text with current word highlighted
                    styled_words = []
                    for j, word_timing_j in enumerate(words_in_caption):
                        word_text = caption_words[j] if j < len(caption_words) else word_timing_j["word"]

                        if j == i:
                            # Current word - use highlight color
                            styled_words.append(f"{{\\c{highlight_color_ass}&}}{word_text}{{\\c{default_color_ass}&}}")
                        else:
                            # Other words - use default color
                            styled_words.append(word_text)

                    styled_text = f"{{\\be1}}{' '.join(styled_words)}"

                    # Write dialogue event for this word
                    start_time = self._format_ass_time(word_start)
                    end_time = self._format_ass_time(word_end)

                    file_handle.write(
                        f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{styled_text}\n"
                    )
            else:
                # Fallback: not enough word timings, use simple caption
                start_time = self._format_ass_time(caption_start)
                end_time = self._format_ass_time(caption_end)
                text = caption_text.replace("\n", "\\N")
                styled_text = f"{{\\be1}}{text}"

                file_handle.write(
                    f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{styled_text}\n"
                )

    def _write_ass(
        self,
        captions: List[Dict[str, Any]],
        output_path: Path,
        video_width: int,
        video_height: int,
        font_size: int,
        word_timings: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Write captions to ASS file with TikTok-style word highlighting.

        ASS format includes:
        - [Script Info]: Video metadata
        - [V4+ Styles]: Style definitions
        - [Events]: Timed captions with word-level highlighting

        Args:
            captions: List of caption dicts
            output_path: Path to write ASS file
            video_width: Video width in pixels
            video_height: Video height in pixels
            font_size: Font size in points
            word_timings: Optional word-level timings for highlighting
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
            f.write(f"WrapStyle: 2\n")  # No word wrapping - text goes as wide as needed
            f.write(f"ScaledBorderAndShadow: yes\n")
            f.write(f"\n")

            # [V4+ Styles] section
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")

            # Default style with viral settings (raised position for TikTok-style)
            margin_v = 100  # Raised from 20 to 100 for higher positioning
            margin_l = 40  # Left margin for wide captions (1200px usable width)
            margin_r = 40  # Right margin for wide captions (1200px usable width)
            f.write(
                f"Style: Default,{self.font_family},{font_size},"
                f"{primary_color},{primary_color},{outline_color},&H00000000,"  # PrimaryColour, SecondaryColour, OutlineColour, BackColour
                f"{bold},0,0,0,"  # Bold, Italic, Underline, StrikeOut
                f"100,100,0,0,"  # ScaleX, ScaleY, Spacing, Angle
                f"1,{self.outline_width},0,"  # BorderStyle, Outline, Shadow
                f"2,{margin_l},{margin_r},{margin_v},1\n"  # Alignment (2=bottom-center), MarginL, MarginR, MarginV, Encoding
            )
            f.write("\n")

            # [Events] section
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

            # Write each caption as dialogue line (with word highlighting if available)
            if self.enable_word_highlight and word_timings:
                # TikTok-style: word-by-word highlighting
                logger.debug("Generating captions with word-level highlighting")
                self._write_highlighted_captions(f, captions, word_timings)
            else:
                # Standard: simple captions without word highlighting
                logger.debug("Generating standard captions without word highlighting")
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
        # Use utility function for color conversion
        return hex_to_ass_bgr(hex_color, alpha=0)

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

    def _validate_font(self) -> None:
        """
        Validate font availability and warn if not found.

        Checks if the specified font is available on the system.
        If not found, logs a warning about fallback to Arial.
        """
        # Skip validation for default fonts
        if self.font_family in ["Arial", "Helvetica", "DejaVu Sans"]:
            logger.debug(f"Using system font: {self.font_family}")
            return

        # Check if font file exists in data/fonts/
        font_dir = Path("data/fonts")
        if font_dir.exists():
            # Look for matching font files
            font_files = list(font_dir.glob(f"{self.font_family}*.ttf")) + \
                         list(font_dir.glob(f"{self.font_family}*.otf"))

            if font_files:
                logger.info(f"Found font file: {font_files[0].name}")
                return

        # Try to check system fonts
        try:
            if platform.system() == "Linux":
                # Use fc-list to check system fonts
                result = subprocess.run(
                    ["fc-list", ":", "family"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if self.font_family.lower() in result.stdout.lower():
                    logger.info(f"Font '{self.font_family}' found in system fonts")
                    return
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # fc-list not available or timed out
            pass

        # Font not found - warn user
        logger.warning(
            f"Font '{self.font_family}' not found. "
            f"Captions will use Arial as fallback. "
            f"For best results, install the font or place it in data/fonts/. "
            f"See data/fonts/README.md for installation instructions."
        )

    def test_readability(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Test caption readability metrics.

        Validates styling parameters against accessibility guidelines (WCAG).
        Returns a report with contrast ratio, font size, and positioning safety.

        Args:
            **kwargs: Additional parameters
                - background_color: Background color for contrast test (default: #000000)

        Returns:
            Dict with readability metrics:
                - contrast_ratio: Text/outline contrast ratio
                - wcag_level: WCAG compliance level (None, AA, AAA)
                - font_size_ok: Whether font size meets minimum (24pt for mobile)
                - position_safe: Whether position avoids UI overlap
                - warnings: List of readability warnings

        Example:
            >>> styler = CaptionStyler(config)
            >>> report = styler.test_readability()
            >>> print(f"Contrast: {report['contrast_ratio']:.1f}:1")
            >>> print(f"WCAG Level: {report['wcag_level']}")
        """
        background_color = kwargs.get("background_color", "#000000")

        # Calculate contrast ratio
        contrast_ratio = calculate_contrast_ratio(self.text_color, self.outline_color)

        # Determine WCAG compliance level
        # Large text (24pt+) needs 3:1 for AA, 4.5:1 for AAA
        if contrast_ratio >= 4.5:
            wcag_level = "AAA"
        elif contrast_ratio >= 3.0:
            wcag_level = "AA"
        else:
            wcag_level = None

        # Check font size (minimum 24pt for mobile)
        font_size_ok = self.font_size >= 24

        # Check position safety (avoid overlapping UI elements)
        # Margins should be at least 20px, avoid top 100px
        margin_v = 20  # Default from ASS style
        position_safe = margin_v >= 20

        # Collect warnings
        warnings = []

        if not wcag_level:
            warnings.append(
                f"Low contrast ratio ({contrast_ratio:.1f}:1). "
                "Recommend 3:1 minimum for large text (WCAG AA)."
            )

        if not font_size_ok:
            warnings.append(
                f"Font size ({self.font_size}pt) below recommended minimum (24pt) "
                "for mobile viewing."
            )

        if not position_safe:
            warnings.append(
                "Caption position may overlap with UI elements. "
                "Increase vertical margin (MarginV >= 20)."
            )

        if self.outline_width < 2:
            warnings.append(
                f"Outline width ({self.outline_width}px) may be too thin. "
                "Recommend 2.5-3px for optimal readability."
            )

        return {
            "contrast_ratio": round(contrast_ratio, 2),
            "wcag_level": wcag_level,
            "font_size": self.font_size,
            "font_size_ok": font_size_ok,
            "position_safe": position_safe,
            "outline_width": self.outline_width,
            "text_color": self.text_color,
            "outline_color": self.outline_color,
            "warnings": warnings,
            "passes_wcag_aa": wcag_level in ["AA", "AAA"],
            "passes_wcag_aaa": wcag_level == "AAA",
        }
