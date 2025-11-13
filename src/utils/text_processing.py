"""
Text Processing Utilities for Script Normalization

Provides functions to clean and normalize scripts for forced alignment.
Handles punctuation removal, case normalization, and special character handling.

Example:
    >>> from src.utils.text_processing import normalize_for_alignment
    >>> text = "Hello, world! (This is AI-powered)."
    >>> normalized = normalize_for_alignment(text)
    >>> print(normalized)
    'hello world this is ai-powered'
"""

import re
from typing import List, Tuple


def normalize_for_alignment(text: str, preserve_case: bool = False) -> str:
    """
    Normalize text for forced alignment.

    Removes brackets, parentheses, and most punctuation while preserving
    apostrophes and hyphens which are important for word boundaries.

    Args:
        text: Raw script text
        preserve_case: If True, keep original case (default: lowercase)

    Returns:
        Normalized text suitable for alignment

    Example:
        >>> normalize_for_alignment("Don't use [brackets] or (parens)!")
        "don't use  or"
    """
    # Remove content in brackets and parentheses
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)

    # Remove special punctuation but keep apostrophes and hyphens
    # Keep: apostrophes ('), hyphens (-)
    # Remove: . , ! ? : ; " « » etc.
    text = re.sub(r'["""«»]', '', text)  # Smart quotes
    text = re.sub(r'[.,!?:;…]', ' ', text)  # Sentence punctuation

    # Convert to lowercase unless preserving case
    if not preserve_case:
        text = text.lower()

    # Normalize whitespace
    text = ' '.join(text.split())

    return text


def split_into_words(text: str) -> List[str]:
    """
    Split normalized text into words.

    Args:
        text: Normalized text

    Returns:
        List of words

    Example:
        >>> split_into_words("hello world this is ai-powered")
        ['hello', 'world', 'this', 'is', 'ai-powered']
    """
    return text.split()


def restore_original_words(aligned_words: List[str], original_text: str) -> List[str]:
    """
    Restore original capitalization and punctuation to aligned words.

    Args:
        aligned_words: List of lowercase normalized words from alignment
        original_text: Original text with proper capitalization

    Returns:
        List of words with original capitalization

    Example:
        >>> aligned = ['hello', 'world']
        >>> original = "Hello, World!"
        >>> restore_original_words(aligned, original)
        ['Hello', 'World']
    """
    # Normalize original for matching
    normalized_original = normalize_for_alignment(original_text, preserve_case=True)
    original_words = split_into_words(normalized_original)

    # Create mapping from lowercase to original
    word_map = {}
    for word in original_words:
        key = word.lower()
        if key not in word_map:
            word_map[key] = word

    # Restore capitalization
    restored = []
    for word in aligned_words:
        restored.append(word_map.get(word.lower(), word))

    return restored


def validate_script_format(text: str) -> Tuple[bool, List[str]]:
    """
    Validate script is suitable for alignment.

    Checks:
    - Not empty
    - Has actual words (not just punctuation)
    - No excessive special characters
    - Reasonable word count (>5 words)

    Args:
        text: Script text to validate

    Returns:
        Tuple of (is_valid, list_of_errors)

    Example:
        >>> validate_script_format("Hello world")
        (True, [])
        >>> validate_script_format("!!!")
        (False, ['Script contains no words'])
    """
    errors = []

    if not text or not text.strip():
        errors.append("Script is empty")
        return False, errors

    # Normalize and count words
    normalized = normalize_for_alignment(text)
    words = split_into_words(normalized)

    if len(words) == 0:
        errors.append("Script contains no words")

    if len(words) < 5:
        errors.append(f"Script too short: {len(words)} words (minimum 5)")

    # Check for excessive special characters
    special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text)
    if special_char_ratio > 0.3:
        errors.append(f"Too many special characters: {special_char_ratio:.1%}")

    return len(errors) == 0, errors


def clean_script_file(file_path: str) -> str:
    """
    Load and clean a script file.

    Handles:
    - UTF-8 encoding
    - Line breaks and paragraph spacing
    - Leading/trailing whitespace
    - BOM (Byte Order Mark)

    Args:
        file_path: Path to script file

    Returns:
        Cleaned script text

    Raises:
        FileNotFoundError: If file doesn't exist
        UnicodeDecodeError: If file is not valid UTF-8
    """
    with open(file_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig removes BOM
        text = f.read()

    # Replace multiple newlines with single space
    text = re.sub(r'\n+', ' ', text)

    # Remove leading/trailing whitespace
    text = text.strip()

    return text


def merge_short_gaps(
    word_timings: List[dict],
    gap_threshold_ms: float = 50.0
) -> List[dict]:
    """
    Merge word timestamps if gap between words is very small.

    Optional post-processing to smooth out micro-pauses that may
    interfere with smooth caption display.

    Args:
        word_timings: List of {word, start, end} dicts
        gap_threshold_ms: Merge if gap < this (milliseconds)

    Returns:
        Smoothed word timings

    Example:
        >>> timings = [
        ...     {"word": "hello", "start": 0.0, "end": 0.5},
        ...     {"word": "world", "start": 0.52, "end": 1.0},  # 20ms gap
        ... ]
        >>> merged = merge_short_gaps(timings, gap_threshold_ms=50)
        >>> merged[0]['end'] == merged[1]['start']  # Gap removed
        True
    """
    if not word_timings:
        return []

    threshold_sec = gap_threshold_ms / 1000.0
    smoothed = [word_timings[0].copy()]

    for i in range(1, len(word_timings)):
        prev = smoothed[-1]
        curr = word_timings[i].copy()

        gap = curr['start'] - prev['end']

        if gap < threshold_sec:
            # Merge gap - extend previous word to touch current
            prev['end'] = curr['start']

        smoothed.append(curr)

    return smoothed
