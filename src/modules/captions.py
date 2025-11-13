"""
Stage 3: Caption Generation

Generates synchronized caption files from alignment data with viral "karaoke effect".

Converts word-level timestamps into one-word-per-caption SRT subtitles optimized
for TikTok/Instagram Reels. Creates addictive reading experience where each word
appears synchronized with audio.

Key Features:
    - One word per caption (viral karaoke effect)
    - Minimum 200ms duration (prevents flicker)
    - Short word merging (<150ms words combined)
    - Seamless transitions (no gaps)
    - Timing validation

Example:
    >>> from src.modules.captions import CaptionGenerator
    >>> generator = CaptionGenerator(config)
    >>> result = generator.process("aligned.json", "captions.srt")
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import Config
from src.core.processor import BaseProcessor, ProcessorResult

logger = logging.getLogger(__name__)


class CaptionError(Exception):
    """Raised when caption generation fails."""
    pass


class CaptionGenerator(BaseProcessor):
    """
    Generate SRT caption files from word-level alignment data.

    Creates viral-style one-word-per-caption subtitles with precise timing.
    Optimized for social media platforms (TikTok, Instagram Reels, YouTube Shorts).

    Output Format (SRT):
        1
        00:00:00,000 --> 00:00:00,500
        Hello

        2
        00:00:00,500 --> 00:00:01,200
        world

    Args:
        config: Configuration object
        temp_dir: Directory for temporary files
    """

    def __init__(self, config: Config, temp_dir: Optional[Path] = None):
        super().__init__(config, temp_dir)

        # Get caption settings from config
        caption_config = getattr(config, "captions", {})
        self.min_duration_ms = getattr(caption_config, "min_duration_ms", 200)
        self.max_duration_ms = getattr(caption_config, "max_duration_ms", 3000)
        self.merge_threshold_ms = getattr(caption_config, "merge_threshold_ms", 150)

    def process(
        self,
        input_path: Path,
        output_path: Path,
        **kwargs: Any,
    ) -> ProcessorResult:
        """
        Generate SRT caption file from alignment JSON.

        Args:
            input_path: Path to alignment JSON from Stage 2
            output_path: Path for SRT output
            **kwargs: Additional parameters
                - words_per_caption: Number of words per caption (default: 1)
                - merge_short_words: Merge words <150ms (default: True)
                - min_duration_ms: Minimum caption duration (default: 200)

        Returns:
            ProcessorResult with SRT file and metadata

        Raises:
            CaptionError: If caption generation fails
        """
        start_time = time.time()
        words_per_caption = kwargs.get("words_per_caption", 1)
        merge_short_words = kwargs.get("merge_short_words", True)
        min_duration_ms = kwargs.get("min_duration_ms", self.min_duration_ms)

        logger.info(f"Starting caption generation: {input_path.name}")
        logger.info(f"Words per caption: {words_per_caption}")
        logger.info(f"Merge short words: {merge_short_words}")

        try:
            # Load alignment JSON
            logger.info(f"Loading alignment data from {input_path}")
            with open(input_path, "r", encoding="utf-8") as f:
                alignment_data = json.load(f)

            if "words" not in alignment_data:
                raise CaptionError("Invalid alignment JSON: missing 'words' field")

            words = alignment_data["words"]
            if not words:
                raise CaptionError("No words found in alignment data")

            logger.info(f"Loaded {len(words)} words")

            # Optionally merge very short words
            if merge_short_words:
                words = self._merge_short_words(words, self.merge_threshold_ms)
                logger.info(f"After merging: {len(words)} captions")

            # Group words into captions
            if words_per_caption == 1:
                captions = words  # One word per caption
            else:
                captions = self._group_words(words, words_per_caption)
                logger.info(f"Grouped into {len(captions)} captions")

            # Enforce minimum duration
            captions = self._enforce_min_duration(captions, min_duration_ms)

            # Validate caption timing
            validation_errors = self._validate_timing(captions)
            if validation_errors:
                for error in validation_errors:
                    logger.warning(f"Timing validation: {error}")

            # Generate SRT file
            logger.info(f"Generating SRT file: {output_path}")
            self._write_srt(captions, output_path)

            # Calculate statistics
            total_duration = captions[-1]["end"] if captions else 0
            avg_duration = sum(c["end"] - c["start"] for c in captions) / len(captions) if captions else 0

            processing_time = time.time() - start_time
            logger.info(f"Caption generation completed in {processing_time:.1f}s")
            logger.info(f"Generated {len(captions)} captions")
            logger.info(f"Total duration: {total_duration:.1f}s")
            logger.info(f"Average caption duration: {avg_duration*1000:.0f}ms")

            return ProcessorResult(
                success=True,
                output_path=output_path,
                metadata={
                    "caption_count": len(captions),
                    "total_duration": round(total_duration, 2),
                    "avg_duration_ms": round(avg_duration * 1000, 0),
                    "processing_time": round(processing_time, 2),
                    "words_per_caption": words_per_caption,
                    "merged": merge_short_words,
                },
            )

        except CaptionError:
            raise
        except Exception as e:
            logger.error(f"Caption generation failed: {e}")
            raise CaptionError(f"Caption generation failed: {e}")

    def _merge_short_words(
        self, words: List[Dict], threshold_ms: float
    ) -> List[Dict]:
        """
        Merge very short words with the next word.

        Words shorter than threshold (e.g., "a", "the", "is") are merged
        with the following word to prevent flickering captions.

        Args:
            words: List of word timing dicts
            threshold_ms: Threshold in milliseconds

        Returns:
            List of merged word timing dicts
        """
        if not words:
            return []

        threshold_sec = threshold_ms / 1000.0
        merged = []
        i = 0

        while i < len(words):
            current = words[i].copy()
            duration = current["end"] - current["start"]

            # If current word is very short and there's a next word, merge them
            if duration < threshold_sec and i + 1 < len(words):
                next_word = words[i + 1]
                current["word"] = f"{current['word']} {next_word['word']}"
                current["end"] = next_word["end"]
                i += 2  # Skip next word since we merged it
                logger.debug(f"Merged short word: '{current['word']}'")
            else:
                i += 1

            merged.append(current)

        return merged

    def _group_words(self, words: List[Dict], words_per_caption: int) -> List[Dict]:
        """
        Group words into multi-word captions.

        Args:
            words: List of word timing dicts
            words_per_caption: Number of words per caption

        Returns:
            List of caption dicts with merged words
        """
        captions = []

        for i in range(0, len(words), words_per_caption):
            group = words[i : i + words_per_caption]
            caption = {
                "word": " ".join(w["word"] for w in group),
                "start": group[0]["start"],
                "end": group[-1]["end"],
            }
            captions.append(caption)

        return captions

    def _enforce_min_duration(
        self, captions: List[Dict], min_duration_ms: float
    ) -> List[Dict]:
        """
        Ensure all captions meet minimum duration requirement.

        Extends caption end time if duration is too short, preventing flicker.

        Args:
            captions: List of caption timing dicts
            min_duration_ms: Minimum duration in milliseconds

        Returns:
            List of captions with enforced minimum duration
        """
        min_duration_sec = min_duration_ms / 1000.0
        adjusted = []

        for i, caption in enumerate(captions):
            caption = caption.copy()
            duration = caption["end"] - caption["start"]

            if duration < min_duration_sec:
                # Extend end time to meet minimum
                new_end = caption["start"] + min_duration_sec

                # Don't overlap with next caption
                if i + 1 < len(captions):
                    next_start = captions[i + 1]["start"]
                    new_end = min(new_end, next_start)

                caption["end"] = new_end
                logger.debug(
                    f"Extended caption '{caption['word'][:20]}...' from {duration*1000:.0f}ms to {(caption['end']-caption['start'])*1000:.0f}ms"
                )

            adjusted.append(caption)

        return adjusted

    def _validate_timing(self, captions: List[Dict]) -> List[str]:
        """
        Validate caption timing for common issues.

        Checks for:
        - Overlapping captions
        - Negative durations
        - Excessively short captions (<100ms)
        - Large gaps (>2s)

        Args:
            captions: List of caption timing dicts

        Returns:
            List of validation error messages
        """
        errors = []

        for i, caption in enumerate(captions):
            # Check duration
            duration = caption["end"] - caption["start"]
            if duration <= 0:
                errors.append(
                    f"Caption {i+1} has invalid duration: {duration*1000:.0f}ms"
                )
            elif duration < 0.1:  # 100ms
                errors.append(
                    f"Caption {i+1} very short: {duration*1000:.0f}ms (may flicker)"
                )

            # Check for overlaps with next caption
            if i + 1 < len(captions):
                next_caption = captions[i + 1]
                if caption["end"] > next_caption["start"]:
                    errors.append(
                        f"Overlap detected: caption {i+1} ends at {caption['end']:.3f}s, "
                        f"but caption {i+2} starts at {next_caption['start']:.3f}s"
                    )

                # Check for large gaps
                gap = next_caption["start"] - caption["end"]
                if gap > 2.0:
                    errors.append(
                        f"Large gap ({gap:.1f}s) between captions {i+1} and {i+2}"
                    )

        return errors

    def _write_srt(self, captions: List[Dict], output_path: Path) -> None:
        """
        Write captions to SRT file.

        SRT format:
            1
            00:00:00,000 --> 00:00:00,500
            Hello

            2
            00:00:00,500 --> 00:00:01,000
            world

        Args:
            captions: List of caption timing dicts
            output_path: Path to write SRT file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            for i, caption in enumerate(captions, start=1):
                # Caption number
                f.write(f"{i}\n")

                # Timestamps in SRT format: HH:MM:SS,mmm --> HH:MM:SS,mmm
                start_time = self._format_srt_time(caption["start"])
                end_time = self._format_srt_time(caption["end"])
                f.write(f"{start_time} --> {end_time}\n")

                # Caption text
                f.write(f"{caption['word']}\n")

                # Blank line separator (except after last caption)
                if i < len(captions):
                    f.write("\n")

        logger.info(f"SRT file saved: {output_path}")

    def _format_srt_time(self, seconds: float) -> str:
        """
        Format time in seconds to SRT format: HH:MM:SS,mmm

        Args:
            seconds: Time in seconds

        Returns:
            Formatted SRT timestamp
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def validate(self, input_path: Path, **kwargs: Any) -> List[str]:
        """
        Validate alignment JSON before caption generation.

        Args:
            input_path: Path to alignment JSON
            **kwargs: Additional parameters

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check file exists
        if not input_path.exists():
            errors.append(f"Alignment file not found: {input_path}")
            return errors

        # Check file is not empty
        if input_path.stat().st_size == 0:
            errors.append("Alignment file is empty")
            return errors

        # Validate JSON structure
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "words" not in data:
                errors.append("Missing 'words' field in alignment JSON")
            elif not data["words"]:
                errors.append("No words in alignment data")
            elif not isinstance(data["words"], list):
                errors.append("'words' field must be a list")
            else:
                # Validate each word entry
                for i, word in enumerate(data["words"]):
                    if not isinstance(word, dict):
                        errors.append(f"Word {i} is not a dict")
                        continue

                    required_fields = ["word", "start", "end"]
                    for field in required_fields:
                        if field not in word:
                            errors.append(f"Word {i} missing field: {field}")

                    # Check timestamps are valid
                    if "start" in word and "end" in word:
                        if not isinstance(word["start"], (int, float)):
                            errors.append(f"Word {i} has invalid start time")
                        if not isinstance(word["end"], (int, float)):
                            errors.append(f"Word {i} has invalid end time")
                        if (
                            isinstance(word["start"], (int, float))
                            and isinstance(word["end"], (int, float))
                            and word["end"] <= word["start"]
                        ):
                            errors.append(
                                f"Word {i} has invalid duration (end <= start)"
                            )

        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")
        except Exception as e:
            errors.append(f"Failed to validate alignment file: {e}")

        return errors

    def estimate_duration(self, input_path: Path, **kwargs: Any) -> float:
        """
        Estimate caption generation duration.

        Caption generation is very fast (typically <1 second for any video).

        Args:
            input_path: Path to alignment file
            **kwargs: Additional parameters

        Returns:
            Estimated time in seconds
        """
        return 1.0  # Caption generation is extremely fast
