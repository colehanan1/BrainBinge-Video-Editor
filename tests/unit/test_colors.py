"""
Unit Tests for Color Utilities

Tests RGB ↔ BGR conversion and WCAG contrast calculations.
"""

import pytest

from src.utils.colors import (
    ass_bgr_to_hex,
    calculate_contrast_ratio,
    hex_to_ass_bgr,
    hex_to_rgb,
    rgb_to_hex,
)


class TestHexToRGB:
    """Test hex_to_rgb() function."""

    def test_full_hex_white(self):
        """Test converting white (#FFFFFF) to RGB."""
        assert hex_to_rgb("#FFFFFF") == (255, 255, 255)

    def test_full_hex_black(self):
        """Test converting black (#000000) to RGB."""
        assert hex_to_rgb("#000000") == (0, 0, 0)

    def test_full_hex_red(self):
        """Test converting red (#FF0000) to RGB."""
        assert hex_to_rgb("#FF0000") == (255, 0, 0)

    def test_full_hex_green(self):
        """Test converting green (#00FF00) to RGB."""
        assert hex_to_rgb("#00FF00") == (0, 255, 0)

    def test_full_hex_blue(self):
        """Test converting blue (#0000FF) to RGB."""
        assert hex_to_rgb("#0000FF") == (0, 0, 255)

    def test_short_hex_format(self):
        """Test converting short hex (#RGB) to RGB."""
        assert hex_to_rgb("#FFF") == (255, 255, 255)
        assert hex_to_rgb("#000") == (0, 0, 0)
        assert hex_to_rgb("#F00") == (255, 0, 0)

    def test_without_hash_prefix(self):
        """Test hex without # prefix."""
        assert hex_to_rgb("FFFFFF") == (255, 255, 255)
        assert hex_to_rgb("FFF") == (255, 255, 255)

    def test_invalid_hex_length(self):
        """Test error on invalid hex length."""
        with pytest.raises(ValueError, match="Invalid hex color"):
            hex_to_rgb("#FF")  # Too short

        with pytest.raises(ValueError, match="Invalid hex color"):
            hex_to_rgb("#FFFFFFF")  # Too long


class TestRGBToHex:
    """Test rgb_to_hex() function."""

    def test_white(self):
        """Test converting white RGB to hex."""
        assert rgb_to_hex(255, 255, 255) == "#FFFFFF"

    def test_black(self):
        """Test converting black RGB to hex."""
        assert rgb_to_hex(0, 0, 0) == "#000000"

    def test_red(self):
        """Test converting red RGB to hex."""
        assert rgb_to_hex(255, 0, 0) == "#FF0000"

    def test_mixed_color(self):
        """Test converting mixed RGB values."""
        assert rgb_to_hex(128, 64, 32) == "#804020"

    def test_invalid_range_high(self):
        """Test error when RGB values exceed 255."""
        with pytest.raises(ValueError, match="must be in range 0-255"):
            rgb_to_hex(256, 0, 0)

    def test_invalid_range_low(self):
        """Test error when RGB values below 0."""
        with pytest.raises(ValueError, match="must be in range 0-255"):
            rgb_to_hex(-1, 0, 0)


class TestHexToASSBGR:
    """Test hex_to_ass_bgr() function."""

    def test_white_opaque(self):
        """Test white with no transparency."""
        assert hex_to_ass_bgr("#FFFFFF") == "&H00FFFFFF"

    def test_black_opaque(self):
        """Test black with no transparency."""
        assert hex_to_ass_bgr("#000000") == "&H00000000"

    def test_red_bgr_conversion(self):
        """Test red converts to BGR format correctly."""
        # Red (#FF0000) should become &H000000FF (BGR = 0000FF)
        assert hex_to_ass_bgr("#FF0000") == "&H000000FF"

    def test_green_bgr_conversion(self):
        """Test green converts to BGR format correctly."""
        # Green (#00FF00) should become &H0000FF00 (BGR = 00FF00)
        assert hex_to_ass_bgr("#00FF00") == "&H0000FF00"

    def test_blue_bgr_conversion(self):
        """Test blue converts to BGR format correctly."""
        # Blue (#0000FF) should become &H00FF0000 (BGR = FF0000)
        assert hex_to_ass_bgr("#0000FF") == "&H00FF0000"

    def test_with_alpha_transparency(self):
        """Test adding alpha/transparency channel."""
        # 50% transparent black (alpha = 128 = 0x80)
        assert hex_to_ass_bgr("#000000", alpha=128) == "&H80000000"

    def test_none_defaults_to_white(self):
        """Test None input defaults to white."""
        assert hex_to_ass_bgr(None) == "&H00FFFFFF"

    def test_invalid_alpha_range(self):
        """Test error when alpha out of range."""
        with pytest.raises(ValueError, match="Alpha must be in range 0-255"):
            hex_to_ass_bgr("#FFFFFF", alpha=256)


class TestASSBGRToHex:
    """Test ass_bgr_to_hex() function."""

    def test_white(self):
        """Test converting ASS white to hex."""
        assert ass_bgr_to_hex("&H00FFFFFF") == "#FFFFFF"

    def test_black(self):
        """Test converting ASS black to hex."""
        assert ass_bgr_to_hex("&H00000000") == "#000000"

    def test_red_bgr_to_rgb(self):
        """Test converting ASS red (BGR) back to RGB hex."""
        assert ass_bgr_to_hex("&H000000FF") == "#FF0000"

    def test_green_bgr_to_rgb(self):
        """Test converting ASS green (BGR) back to RGB hex."""
        assert ass_bgr_to_hex("&H0000FF00") == "#00FF00"

    def test_blue_bgr_to_rgb(self):
        """Test converting ASS blue (BGR) back to RGB hex."""
        assert ass_bgr_to_hex("&H00FF0000") == "#0000FF"

    def test_with_transparency(self):
        """Test ASS color with alpha channel."""
        # Should ignore alpha and return RGB hex
        assert ass_bgr_to_hex("&H80000000") == "#000000"

    def test_invalid_format(self):
        """Test error on invalid ASS color format."""
        with pytest.raises(ValueError, match="Invalid ASS color"):
            ass_bgr_to_hex("&HFF")  # Too short


class TestContrastRatio:
    """Test calculate_contrast_ratio() function."""

    def test_black_white_max_contrast(self):
        """Test black/white has maximum contrast (21:1)."""
        ratio = calculate_contrast_ratio("#FFFFFF", "#000000")
        assert ratio == pytest.approx(21.0, rel=0.01)

    def test_same_color_no_contrast(self):
        """Test same color has no contrast (1:1)."""
        ratio = calculate_contrast_ratio("#FFFFFF", "#FFFFFF")
        assert ratio == pytest.approx(1.0, rel=0.01)

        ratio = calculate_contrast_ratio("#000000", "#000000")
        assert ratio == pytest.approx(1.0, rel=0.01)

    def test_order_independent(self):
        """Test contrast ratio is same regardless of order."""
        ratio1 = calculate_contrast_ratio("#FFFFFF", "#808080")
        ratio2 = calculate_contrast_ratio("#808080", "#FFFFFF")
        assert ratio1 == pytest.approx(ratio2, rel=0.01)

    def test_wcag_aa_threshold(self):
        """Test colors meeting WCAG AA threshold (4.5:1)."""
        # White text on medium gray should meet AA
        ratio = calculate_contrast_ratio("#FFFFFF", "#767676")
        assert ratio >= 4.5

    def test_wcag_aaa_threshold(self):
        """Test colors meeting WCAG AAA threshold (7:1)."""
        # White text on dark gray should meet AAA
        ratio = calculate_contrast_ratio("#FFFFFF", "#595959")
        assert ratio >= 7.0

    def test_caption_colors(self):
        """Test typical caption color combination (white text, black outline)."""
        ratio = calculate_contrast_ratio("#FFFFFF", "#000000")
        assert ratio >= 7.0  # Exceeds WCAG AAA


class TestColorPresets:
    """Test predefined color constants."""

    def test_colors_dict_exists(self):
        """Test COLORS dict is available."""
        from src.utils.colors import COLORS

        assert "white" in COLORS
        assert "black" in COLORS
        assert "red" in COLORS

    def test_ass_colors_dict_exists(self):
        """Test ASS_COLORS dict is available."""
        from src.utils.colors import ASS_COLORS

        assert "white" in ASS_COLORS
        assert "black" in ASS_COLORS
        assert ASS_COLORS["white"] == "&H00FFFFFF"
        assert ASS_COLORS["black"] == "&H00000000"

    def test_social_media_colors(self):
        """Test social media brand colors are defined."""
        from src.utils.colors import COLORS

        assert "tiktok_pink" in COLORS
        assert "tiktok_cyan" in COLORS
        assert "instagram_purple" in COLORS
        assert "youtube_red" in COLORS


class TestRoundTripConversion:
    """Test round-trip conversions maintain values."""

    def test_hex_to_rgb_to_hex(self):
        """Test hex → RGB → hex preserves value."""
        original = "#FF8800"
        r, g, b = hex_to_rgb(original)
        result = rgb_to_hex(r, g, b)
        assert result == original

    def test_hex_to_ass_to_hex(self):
        """Test hex → ASS BGR → hex preserves value."""
        original = "#FF8800"
        ass_color = hex_to_ass_bgr(original)
        result = ass_bgr_to_hex(ass_color)
        assert result == original

    def test_multiple_colors(self):
        """Test round-trip for various colors."""
        colors = ["#FFFFFF", "#000000", "#FF0000", "#00FF00", "#0000FF", "#ABCDEF"]

        for color in colors:
            ass_color = hex_to_ass_bgr(color)
            result = ass_bgr_to_hex(ass_color)
            assert result == color
