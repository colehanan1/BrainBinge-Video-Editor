"""
Unit Tests for Caption Styling Module

Tests SRT → ASS conversion with viral styling effects.
"""

import json
import pytest
from pathlib import Path

from src.config import AudioConfig, BRollConfig, BrandConfig, CaptionConfig, Config, ExportConfig
from src.modules.styling import CaptionStyler, StylingError


@pytest.fixture
def sample_config():
    """Create sample configuration."""
    return Config(
        brand=BrandConfig(name="Test Brand"),
        captions=CaptionConfig(),
        broll=BRollConfig(),
        audio=AudioConfig(),
        export=ExportConfig(),
    )


@pytest.fixture
def custom_style_config():
    """Create configuration with custom styling."""
    from src.config import FontConfig, CaptionStyleConfig

    return Config(
        brand=BrandConfig(name="Test Brand"),
        captions=CaptionConfig(
            font=FontConfig(
                family="Montserrat-Bold",
                size=30,
                weight="bold"
            ),
            style=CaptionStyleConfig(
                color="#FFD700",  # Gold
                stroke_color="#000000",
                stroke_width=4
            )
        ),
        broll=BRollConfig(),
        audio=AudioConfig(),
        export=ExportConfig(),
    )


@pytest.fixture
def sample_srt_file(tmp_path):
    """Create a sample SRT file."""
    srt_content = """1
00:00:00,000 --> 00:00:00,500
Hello

2
00:00:00,500 --> 00:00:01,000
world

3
00:00:01,000 --> 00:00:01,500
this

4
00:00:01,500 --> 00:00:02,000
is

5
00:00:02,000 --> 00:00:02,500
a

6
00:00:02,500 --> 00:00:03,000
test
"""
    srt_path = tmp_path / "captions.srt"
    srt_path.write_text(srt_content, encoding="utf-8")
    return srt_path


@pytest.fixture
def temp_output(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


class TestCaptionStylerInit:
    """Test CaptionStyler initialization."""

    def test_init_with_defaults(self, sample_config):
        """Test initialization with default config."""
        styler = CaptionStyler(sample_config)

        assert styler.font_family == "Arial"
        assert styler.font_size == 28
        assert styler.font_weight == "bold"
        assert styler.text_color == "#FFFFFF"
        assert styler.outline_color == "#000000"
        assert styler.outline_width == 3

    def test_init_with_custom_font(self, custom_style_config):
        """Test initialization with custom font config."""
        styler = CaptionStyler(custom_style_config)

        assert styler.font_family == "Montserrat-Bold"
        assert styler.font_size == 30
        assert styler.text_color == "#FFD700"
        assert styler.outline_width == 4

    def test_video_dimensions_default(self, sample_config):
        """Test default video dimensions."""
        styler = CaptionStyler(sample_config)

        assert styler.video_width == 1280
        assert styler.video_height == 720


class TestSRTToASSConversion:
    """Test SRT → ASS conversion."""

    def test_basic_conversion(self, sample_config, sample_srt_file, temp_output):
        """Test basic SRT to ASS conversion."""
        styler = CaptionStyler(sample_config)
        output_path = temp_output / "styled.ass"

        result = styler.process(sample_srt_file, output_path)

        assert result.success is True
        assert output_path.exists()
        assert result.metadata["caption_count"] == 6

    def test_ass_file_structure(self, sample_config, sample_srt_file, temp_output):
        """Test ASS file has correct structure."""
        styler = CaptionStyler(sample_config)
        output_path = temp_output / "styled.ass"

        styler.process(sample_srt_file, output_path)

        content = output_path.read_text(encoding="utf-8")

        # Check for required ASS sections
        assert "[Script Info]" in content
        assert "[V4+ Styles]" in content
        assert "[Events]" in content

        # Check for style definition
        assert "Style: Default" in content
        assert "Arial" in content  # Default font

    def test_blur_effect_applied(self, sample_config, sample_srt_file, temp_output):
        """Test blur effect (\\be1) is applied to captions."""
        styler = CaptionStyler(sample_config)
        output_path = temp_output / "styled.ass"

        styler.process(sample_srt_file, output_path)

        content = output_path.read_text(encoding="utf-8")

        # Check for blur effect in dialogue lines
        assert "{\\be1}" in content

        # Each caption should have blur effect
        dialogue_lines = [line for line in content.split('\n') if line.startswith('Dialogue:')]
        for line in dialogue_lines:
            assert "{\\be1}" in line

    def test_caption_text_preserved(self, sample_config, sample_srt_file, temp_output):
        """Test caption text is preserved from SRT."""
        styler = CaptionStyler(sample_config)
        output_path = temp_output / "styled.ass"

        styler.process(sample_srt_file, output_path)

        content = output_path.read_text(encoding="utf-8")

        # Check all words are present
        assert "Hello" in content
        assert "world" in content
        assert "this" in content
        assert "is" in content
        assert "test" in content

    def test_timing_preserved(self, sample_config, sample_srt_file, temp_output):
        """Test caption timing is preserved during conversion."""
        styler = CaptionStyler(sample_config)
        output_path = temp_output / "styled.ass"

        styler.process(sample_srt_file, output_path)

        content = output_path.read_text(encoding="utf-8")

        # Check for ASS timestamp format (H:MM:SS.cc)
        # First caption: 0:00:00.00 → 0:00:00.50
        assert "0:00:00.00" in content
        assert "0:00:00.50" in content

    def test_custom_video_dimensions(self, sample_config, sample_srt_file, temp_output):
        """Test custom video dimensions."""
        styler = CaptionStyler(sample_config)
        output_path = temp_output / "styled.ass"

        result = styler.process(
            sample_srt_file,
            output_path,
            video_width=1920,
            video_height=1080
        )

        assert result.success is True
        assert result.metadata["video_resolution"] == "1920×1080"

        content = output_path.read_text(encoding="utf-8")
        assert "PlayResX: 1920" in content
        assert "PlayResY: 1080" in content


class TestColorConversion:
    """Test color conversion to ASS BGR format."""

    def test_white_color_bgr(self, sample_config, sample_srt_file, temp_output):
        """Test white color converts to BGR correctly."""
        styler = CaptionStyler(sample_config)
        output_path = temp_output / "styled.ass"

        styler.process(sample_srt_file, output_path)

        content = output_path.read_text(encoding="utf-8")

        # White in ASS BGR format: &H00FFFFFF
        assert "&H00FFFFFF" in content

    def test_black_outline_bgr(self, sample_config, sample_srt_file, temp_output):
        """Test black outline converts to BGR correctly."""
        styler = CaptionStyler(sample_config)
        output_path = temp_output / "styled.ass"

        styler.process(sample_srt_file, output_path)

        content = output_path.read_text(encoding="utf-8")

        # Black in ASS BGR format: &H00000000
        assert "&H00000000" in content

    def test_custom_colors(self, custom_style_config, sample_srt_file, temp_output):
        """Test custom colors are applied."""
        styler = CaptionStyler(custom_style_config)
        output_path = temp_output / "styled.ass"

        styler.process(sample_srt_file, output_path)

        # Gold (#FFD700) should be in the file
        # In BGR format: &H0000D7FF
        content = output_path.read_text(encoding="utf-8")
        assert "&H0000D7FF" in content  # Gold in BGR


class TestReadability:
    """Test caption readability metrics."""

    def test_readability_report_structure(self, sample_config):
        """Test readability report has expected fields."""
        styler = CaptionStyler(sample_config)
        report = styler.test_readability()

        # Check all expected fields are present
        assert "contrast_ratio" in report
        assert "wcag_level" in report
        assert "font_size" in report
        assert "font_size_ok" in report
        assert "position_safe" in report
        assert "outline_width" in report
        assert "warnings" in report
        assert "passes_wcag_aa" in report
        assert "passes_wcag_aaa" in report

    def test_default_style_passes_wcag(self, sample_config):
        """Test default styling meets WCAG guidelines."""
        styler = CaptionStyler(sample_config)
        report = styler.test_readability()

        # White text on black outline should have max contrast (21:1)
        assert report["contrast_ratio"] == 21.0
        assert report["wcag_level"] == "AAA"
        assert report["passes_wcag_aa"] is True
        assert report["passes_wcag_aaa"] is True

    def test_font_size_check(self, sample_config):
        """Test font size readability check."""
        styler = CaptionStyler(sample_config)
        report = styler.test_readability()

        # Default 28pt should pass minimum 24pt for mobile
        assert report["font_size"] == 28
        assert report["font_size_ok"] is True
        assert len([w for w in report["warnings"] if "font size" in w.lower()]) == 0

    def test_small_font_warning(self):
        """Test warning for font size below 24pt."""
        from src.config import FontConfig

        config = Config(
            brand=BrandConfig(name="Test"),
            captions=CaptionConfig(
                font=FontConfig(family="Arial", size=18)  # Below minimum
            ),
            broll=BRollConfig(),
            audio=AudioConfig(),
            export=ExportConfig(),
        )

        styler = CaptionStyler(config)
        report = styler.test_readability()

        assert report["font_size_ok"] is False
        assert any("font size" in w.lower() for w in report["warnings"])

    def test_thin_outline_warning(self):
        """Test warning for outline width below 2px."""
        from src.config import CaptionStyleConfig

        config = Config(
            brand=BrandConfig(name="Test"),
            captions=CaptionConfig(
                style=CaptionStyleConfig(stroke_width=1)  # Too thin
            ),
            broll=BRollConfig(),
            audio=AudioConfig(),
            export=ExportConfig(),
        )

        styler = CaptionStyler(config)
        report = styler.test_readability()

        assert any("outline width" in w.lower() for w in report["warnings"])


class TestValidation:
    """Test input validation."""

    def test_validate_srt_file_exists(self, sample_config, sample_srt_file):
        """Test validation passes for existing SRT file."""
        styler = CaptionStyler(sample_config)
        errors = styler.validate(sample_srt_file)

        assert len(errors) == 0

    def test_validate_missing_file(self, sample_config, tmp_path):
        """Test validation fails for missing file."""
        styler = CaptionStyler(sample_config)
        missing_file = tmp_path / "nonexistent.srt"

        errors = styler.validate(missing_file)

        assert len(errors) > 0
        assert any("not found" in e.lower() for e in errors)

    def test_validate_empty_file(self, sample_config, tmp_path):
        """Test validation fails for empty file."""
        styler = CaptionStyler(sample_config)
        empty_file = tmp_path / "empty.srt"
        empty_file.write_text("", encoding="utf-8")

        errors = styler.validate(empty_file)

        assert len(errors) > 0
        assert any("empty" in e.lower() for e in errors)

    def test_validate_invalid_srt_format(self, sample_config, tmp_path):
        """Test validation fails for invalid SRT format."""
        styler = CaptionStyler(sample_config)
        invalid_file = tmp_path / "invalid.srt"
        invalid_file.write_text("This is not an SRT file", encoding="utf-8")

        errors = styler.validate(invalid_file)

        assert len(errors) > 0
        assert any("timestamp" in e.lower() or "format" in e.lower() for e in errors)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_single_caption(self, sample_config, tmp_path, temp_output):
        """Test converting SRT with single caption."""
        srt_content = """1
00:00:00,000 --> 00:00:01,000
Single
"""
        srt_path = tmp_path / "single.srt"
        srt_path.write_text(srt_content, encoding="utf-8")

        styler = CaptionStyler(sample_config)
        output_path = temp_output / "single.ass"

        result = styler.process(srt_path, output_path)

        assert result.success is True
        assert result.metadata["caption_count"] == 1

    def test_multiline_caption(self, sample_config, tmp_path, temp_output):
        """Test caption with multiple lines."""
        srt_content = """1
00:00:00,000 --> 00:00:01,000
Line one
Line two
"""
        srt_path = tmp_path / "multiline.srt"
        srt_path.write_text(srt_content, encoding="utf-8")

        styler = CaptionStyler(sample_config)
        output_path = temp_output / "multiline.ass"

        result = styler.process(srt_path, output_path)

        assert result.success is True

        # Check that newlines are converted to ASS line breaks (\\N)
        content = output_path.read_text(encoding="utf-8")
        assert "\\N" in content

    def test_utf8_characters(self, sample_config, tmp_path, temp_output):
        """Test captions with UTF-8 characters."""
        srt_content = """1
00:00:00,000 --> 00:00:01,000
Café

2
00:00:01,000 --> 00:00:02,000
résumé

3
00:00:02,000 --> 00:00:03,000
naïve
"""
        srt_path = tmp_path / "utf8.srt"
        srt_path.write_text(srt_content, encoding="utf-8")

        styler = CaptionStyler(sample_config)
        output_path = temp_output / "utf8.ass"

        result = styler.process(srt_path, output_path)

        assert result.success is True

        content = output_path.read_text(encoding="utf-8")
        assert "Café" in content
        assert "résumé" in content
        assert "naïve" in content

    def test_empty_srt_file(self, sample_config, tmp_path, temp_output):
        """Test error on empty SRT file."""
        srt_path = tmp_path / "empty.srt"
        srt_path.write_text("", encoding="utf-8")

        styler = CaptionStyler(sample_config)
        output_path = temp_output / "output.ass"

        with pytest.raises(StylingError, match="No captions found"):
            styler.process(srt_path, output_path)


class TestMetadata:
    """Test metadata in ProcessorResult."""

    def test_metadata_fields(self, sample_config, sample_srt_file, temp_output):
        """Test all expected metadata fields are present."""
        styler = CaptionStyler(sample_config)
        output_path = temp_output / "styled.ass"

        result = styler.process(sample_srt_file, output_path)

        assert "caption_count" in result.metadata
        assert "video_resolution" in result.metadata
        assert "font" in result.metadata
        assert "processing_time" in result.metadata

    def test_metadata_values(self, sample_config, sample_srt_file, temp_output):
        """Test metadata values are correct."""
        styler = CaptionStyler(sample_config)
        output_path = temp_output / "styled.ass"

        result = styler.process(sample_srt_file, output_path)

        assert result.metadata["caption_count"] == 6
        assert result.metadata["video_resolution"] == "1280×720"
        assert "Arial" in result.metadata["font"]
        assert "28pt" in result.metadata["font"]
        assert result.metadata["processing_time"] >= 0


class TestEstimateDuration:
    """Test duration estimation."""

    def test_estimate_is_fast(self, sample_config, sample_srt_file):
        """Test styling duration estimate is very short."""
        styler = CaptionStyler(sample_config)
        estimate = styler.estimate_duration(sample_srt_file)

        # Styling is extremely fast (<1 second)
        assert estimate <= 1.0
