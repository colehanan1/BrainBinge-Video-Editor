"""
Stage 2: Force Alignment

Aligns script text with audio timing using forcealign library.

Generates word-level timestamps with ±50ms accuracy using forced alignment.
Since we have the exact script, this is faster and more accurate than transcription.

Key Features:
    - Word-level timestamp accuracy (±50ms)
    - 95%+ coverage expected
    - Handles punctuation normalization
    - Graceful degradation on alignment failure

Example:
    >>> from src.modules.alignment import ForceAligner
    >>> aligner = ForceAligner(config)
    >>> result = aligner.process("audio.wav", "aligned.json", "script.txt")
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import Config
from src.core.processor import BaseProcessor, ProcessorResult
from src.utils.text_processing import (
    clean_script_file,
    merge_short_gaps,
    normalize_for_alignment,
    restore_original_words,
    split_into_words,
    validate_script_format,
)

logger = logging.getLogger(__name__)


class AlignmentError(Exception):
    """Raised when alignment fails."""

    pass


class ForceAligner(BaseProcessor):
    """
    Force alignment of script text with audio timing.

    Uses forcealign library to generate word-level timestamps matching
    script text to audio. This is faster than transcription since we
    have the exact script.

    Output Format (JSON):
        {
            "words": [
                {"word": "Hello", "start": 0.0, "end": 0.5},
                {"word": "world", "start": 0.5, "end": 1.0}
            ],
            "coverage": 0.98,
            "word_count": 2
        }

    Args:
        config: Configuration object
        temp_dir: Directory for temporary files
    """

    def __init__(self, config: Config, temp_dir: Optional[Path] = None):
        super().__init__(config, temp_dir)
        self.model_name = getattr(config, "alignment", {}).get("model", "base")
        self.language = getattr(config, "alignment", {}).get("language", "en")

    def process(
        self,
        input_path: Path,
        output_path: Path,
        script_path: Path,
        **kwargs: Any,
    ) -> ProcessorResult:
        """
        Perform force alignment.

        Args:
            input_path: Path to audio file (WAV, 16kHz)
            output_path: Path for alignment output (JSON)
            script_path: Path to script text file
            **kwargs: Additional parameters
                - smooth_gaps: Merge gaps < 50ms (default: True)
                - min_coverage: Minimum coverage to succeed (default: 0.5)

        Returns:
            ProcessorResult with alignment JSON and metadata

        Raises:
            AlignmentError: If alignment coverage < min_coverage
            FileNotFoundError: If audio or script file missing
        """
        start_time = time.time()
        smooth_gaps = kwargs.get("smooth_gaps", True)
        min_coverage = kwargs.get("min_coverage", 0.5)

        logger.info(f"Starting force alignment: {input_path.name}")

        try:
            # Load and validate script
            logger.info(f"Loading script from {script_path}")
            script_text = clean_script_file(str(script_path))

            is_valid, errors = validate_script_format(script_text)
            if not is_valid:
                raise ValueError(f"Invalid script format: {'; '.join(errors)}")

            logger.info(f"Script length: {len(script_text)} chars")

            # Normalize script for alignment
            normalized_script = normalize_for_alignment(script_text)
            expected_words = split_into_words(normalized_script)
            logger.info(f"Expected words: {len(expected_words)}")

            # Import forcealign (lazy import in case models not installed)
            try:
                from forcealign import ForceAlign
            except ImportError:
                raise RuntimeError(
                    "forcealign library not installed. "
                    "Install with: pip install forcealign"
                )

            # Initialize aligner
            # Note: ForceAlign only supports English, language parameter not available
            logger.info("Initializing ForceAlign for English")
            aligner = ForceAlign(
                audio_file=str(input_path),
                transcript=normalized_script,
            )

            # Run alignment
            logger.info("Running forced alignment...")
            aligned_words = aligner.inference()

            # Convert to our format
            word_timings = []
            for word_obj in aligned_words:
                word_timings.append(
                    {
                        "word": word_obj.word,
                        "start": round(word_obj.time_start, 3),
                        "end": round(word_obj.time_end, 3),
                    }
                )

            logger.info(f"Aligned words: {len(word_timings)}")

            # Calculate coverage
            coverage = len(word_timings) / len(expected_words) if expected_words else 0
            logger.info(f"Alignment coverage: {coverage:.1%}")

            # Check coverage threshold
            if coverage < min_coverage:
                raise AlignmentError(
                    f"Alignment coverage too low: {coverage:.1%} < {min_coverage:.1%}. "
                    f"Script may not match audio. Expected {len(expected_words)} words, "
                    f"got {len(word_timings)}."
                )

            if coverage < 0.8:
                logger.warning(
                    f"Low alignment coverage: {coverage:.1%}. "
                    "Some words may be missing. Verify script matches audio."
                )

            # Restore original capitalization
            aligned_word_list = [w["word"] for w in word_timings]
            restored_words = restore_original_words(aligned_word_list, script_text)

            for i, timing in enumerate(word_timings):
                timing["word"] = restored_words[i]

            # Smooth gaps if requested
            if smooth_gaps:
                logger.info("Smoothing short gaps (<50ms)")
                word_timings = merge_short_gaps(word_timings, gap_threshold_ms=50.0)

            # Post-processing validation
            validation_errors = self._validate_timings(word_timings)
            if validation_errors:
                for error in validation_errors:
                    logger.warning(f"Timing validation: {error}")

            # Prepare output
            output_data = {
                "words": word_timings,
                "coverage": round(coverage, 3),
                "word_count": len(word_timings),
                "expected_words": len(expected_words),
                "audio_file": input_path.name,
                "script_file": script_path.name,
            }

            # Save JSON
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            processing_time = time.time() - start_time
            logger.info(f"Alignment completed in {processing_time:.1f}s")
            logger.info(f"Output saved to: {output_path}")

            return ProcessorResult(
                success=True,
                output_path=output_path,
                metadata={
                    "word_count": len(word_timings),
                    "expected_words": len(expected_words),
                    "coverage": coverage,
                    "processing_time": round(processing_time, 2),
                    "smoothed": smooth_gaps,
                },
            )

        except AlignmentError:
            raise
        except Exception as e:
            logger.error(f"Force alignment failed: {e}")
            raise RuntimeError(f"Force alignment failed: {e}")

    def _validate_timings(self, word_timings: List[Dict]) -> List[str]:
        """
        Validate word timings for common issues.

        Checks for:
        - Overlapping timestamps
        - Large gaps (>2s) indicating alignment problems
        - Negative durations

        Args:
            word_timings: List of word timing dicts

        Returns:
            List of validation error messages
        """
        errors = []

        for i, timing in enumerate(word_timings):
            # Check duration
            duration = timing["end"] - timing["start"]
            if duration <= 0:
                errors.append(
                    f"Word {i} '{timing['word']}' has invalid duration: {duration}s"
                )

            # Check for overlaps with next word
            if i < len(word_timings) - 1:
                next_timing = word_timings[i + 1]
                if timing["end"] > next_timing["start"]:
                    errors.append(
                        f"Overlap detected: '{timing['word']}' ends at {timing['end']}, "
                        f"but '{next_timing['word']}' starts at {next_timing['start']}"
                    )

                # Check for large gaps
                gap = next_timing["start"] - timing["end"]
                if gap > 2.0:
                    errors.append(
                        f"Large gap ({gap:.1f}s) between '{timing['word']}' and '{next_timing['word']}'"
                    )

        return errors

    def validate(self, input_path: Path, script_path: Path, **kwargs: Any) -> List[str]:
        """
        Validate audio and script files before alignment.

        Args:
            input_path: Path to audio file
            script_path: Path to script file
            **kwargs: Additional parameters

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check audio file
        if not input_path.exists():
            errors.append(f"Audio file not found: {input_path}")
        elif input_path.suffix.lower() != ".wav":
            errors.append(f"Audio must be WAV format, got: {input_path.suffix}")
        elif input_path.stat().st_size == 0:
            errors.append("Audio file is empty")

        # Check script file
        if not script_path.exists():
            errors.append(f"Script file not found: {script_path}")
        elif script_path.stat().st_size == 0:
            errors.append("Script file is empty")
        else:
            # Validate script content
            try:
                script_text = clean_script_file(str(script_path))
                is_valid, script_errors = validate_script_format(script_text)
                if not is_valid:
                    errors.extend(script_errors)
            except Exception as e:
                errors.append(f"Failed to read script: {e}")

        return errors

    def estimate_duration(self, input_path: Path, **kwargs: Any) -> float:
        """
        Estimate alignment processing time.

        Args:
            input_path: Path to audio file

        Returns:
            Estimated time in seconds (~50-100% of audio duration)
        """
        try:
            import ffmpeg

            # Get audio duration
            probe = ffmpeg.probe(str(input_path))
            duration = float(probe["format"]["duration"])

            # Alignment typically takes 0.5-1x audio duration
            # First run may be slower due to model loading
            return duration * 0.75
        except Exception:
            # Fallback estimate
            return 30.0
