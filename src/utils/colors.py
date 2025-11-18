"""
Color Conversion Utilities

Provides RGB ↔ BGR conversion helpers for ASS subtitle format.

ASS uses BGR (Blue-Green-Red) color format instead of RGB:
- Format: &H[AA][BB][GG][RR] (alpha, blue, green, red)
- Example: White = &H00FFFFFF, Black = &H00000000
"""

from typing import Tuple, Union


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert hex color (#RRGGBB) to RGB tuple.

    Args:
        hex_color: Hex color string (#RRGGBB or #RGB)

    Returns:
        Tuple of (red, green, blue) values (0-255)

    Example:
        >>> hex_to_rgb("#FFFFFF")
        (255, 255, 255)
        >>> hex_to_rgb("#F00")
        (255, 0, 0)
    """
    hex_color = hex_color.lstrip('#')

    # Expand short form (#RGB → #RRGGBB)
    if len(hex_color) == 3:
        hex_color = ''.join([c * 2 for c in hex_color])

    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: #{hex_color}")

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    return (r, g, b)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Convert RGB values to hex color (#RRGGBB).

    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)

    Returns:
        Hex color string (#RRGGBB)

    Example:
        >>> rgb_to_hex(255, 255, 255)
        '#FFFFFF'
        >>> rgb_to_hex(255, 0, 0)
        '#FF0000'
    """
    if not all(0 <= val <= 255 for val in [r, g, b]):
        raise ValueError("RGB values must be in range 0-255")

    return f"#{r:02X}{g:02X}{b:02X}"


def hex_to_ass_bgr(hex_color: str, alpha: int = 0) -> str:
    """
    Convert hex color (#RRGGBB) to ASS BGR format (&H00BBGGRR).

    ASS uses BGR (Blue-Green-Red) instead of RGB, with alpha channel.

    Args:
        hex_color: Hex color string (#RRGGBB or #RGB)
        alpha: Alpha/opacity value (0-255, 0=opaque, 255=transparent)

    Returns:
        ASS color string (&HAABBGGRR)

    Example:
        >>> hex_to_ass_bgr("#FFFFFF")
        '&H00FFFFFF'
        >>> hex_to_ass_bgr("#FF0000")  # Red
        '&H000000FF'
        >>> hex_to_ass_bgr("#000000", alpha=128)  # 50% transparent black
        '&H80000000'
    """
    if hex_color is None:
        hex_color = "#FFFFFF"  # Default to white

    r, g, b = hex_to_rgb(hex_color)

    if not 0 <= alpha <= 255:
        raise ValueError("Alpha must be in range 0-255")

    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}"


def ass_bgr_to_hex(ass_color: str) -> str:
    """
    Convert ASS BGR format (&H00BBGGRR) to hex color (#RRGGBB).

    Args:
        ass_color: ASS color string (&HAABBGGRR)

    Returns:
        Hex color string (#RRGGBB)

    Example:
        >>> ass_bgr_to_hex("&H00FFFFFF")
        '#FFFFFF'
        >>> ass_bgr_to_hex("&H000000FF")  # Red
        '#FF0000'
    """
    # Remove &H prefix
    ass_color = ass_color.replace('&H', '')

    if len(ass_color) != 8:
        raise ValueError(f"Invalid ASS color: &H{ass_color}")

    # Extract BGR values (skip alpha)
    alpha = int(ass_color[0:2], 16)
    b = int(ass_color[2:4], 16)
    g = int(ass_color[4:6], 16)
    r = int(ass_color[6:8], 16)

    return rgb_to_hex(r, g, b)


def calculate_contrast_ratio(color1: str, color2: str) -> float:
    """
    Calculate WCAG contrast ratio between two colors.

    Args:
        color1: First hex color (#RRGGBB)
        color2: Second hex color (#RRGGBB)

    Returns:
        Contrast ratio (1.0-21.0)

    WCAG Guidelines:
        - AA: 4.5:1 for normal text, 3:1 for large text
        - AAA: 7:1 for normal text, 4.5:1 for large text

    Example:
        >>> calculate_contrast_ratio("#FFFFFF", "#000000")
        21.0
        >>> calculate_contrast_ratio("#FFFFFF", "#FFFFFF")
        1.0
    """
    def relative_luminance(r: int, g: int, b: int) -> float:
        """Calculate relative luminance (WCAG formula)."""
        def adjust(val: int) -> float:
            val = val / 255.0
            if val <= 0.03928:
                return val / 12.92
            else:
                return ((val + 0.055) / 1.055) ** 2.4

        return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)

    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)

    l1 = relative_luminance(r1, g1, b1)
    l2 = relative_luminance(r2, g2, b2)

    # Ensure l1 is the lighter color
    if l2 > l1:
        l1, l2 = l2, l1

    return (l1 + 0.05) / (l2 + 0.05)


# Common color presets (hex format)
COLORS = {
    # Basic colors
    "white": "#FFFFFF",
    "black": "#000000",
    "red": "#FF0000",
    "green": "#00FF00",
    "blue": "#0000FF",
    "yellow": "#FFFF00",
    "cyan": "#00FFFF",
    "magenta": "#FF00FF",

    # Social media brand colors
    "tiktok_pink": "#FE2C55",
    "tiktok_cyan": "#25F4EE",
    "instagram_purple": "#C13584",
    "youtube_red": "#FF0000",

    # Caption styling presets
    "caption_white": "#FFFFFF",
    "caption_yellow": "#FFD700",  # Gold
    "outline_black": "#000000",
    "shadow_gray": "#1A1A1A",
}


# Common ASS color presets
ASS_COLORS = {
    "white": "&H00FFFFFF",
    "black": "&H00000000",
    "red": "&H000000FF",
    "green": "&H0000FF00",
    "blue": "&H00FF0000",
    "yellow": "&H0000FFFF",

    # With transparency (50% opacity)
    "semi_black": "&H80000000",
    "semi_white": "&H80FFFFFF",
}
