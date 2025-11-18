"""
Unit tests for Stage 2: Force Alignment

Tests ForceAligner integration with word-level timestamp generation.

Test Coverage:
    - Normal alignment with 30-word script
    - Punctuation removal and restoration
    - Alignment failure handling (low coverage)
    - JSON output format validation
    - Coverage threshold warnings and errors
    - Gap smoothing functionality
    - Timing validation (overlaps, large gaps)
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from src.config import Config
from src.modules.alignment import AlignmentError, ForceAligner


class MockWordObj:
    """Mock object for forcealign word results."""

    def __init__(self, word: str, start: float, end: float):
        self.word = word
        self.time_start = start
        self.time_end = end


@pytest.fixture
def sample_config():
    """Create sample configuration."""
    from src.config import BrandConfig, CaptionConfig, BRollConfig, AudioConfig, ExportConfig

    return Config(
        brand=BrandConfig(name="Test Brand"),
        captions=CaptionConfig(),
        broll=BRollConfig(),
        audio=AudioConfig(),
        export=ExportConfig(),
    )


@pytest.fixture
def temp_output(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_script_30_words():
    """30-word sample script with punctuation."""
    return (
        "This is a sample script for testing forced alignment. "
        "It contains exactly thirty words including punctuation marks, "
        "apostrophes like don't, and hyphens in AI-powered technology!"
    )


@pytest.fixture
def sample_audio_path(tmp_path):
    """Create mock audio file path."""
    audio_path = tmp_path / "audio.wav"
    audio_path.write_bytes(b"FAKE_WAV_DATA")
    return audio_path


@pytest.fixture
def sample_script_path(tmp_path, sample_script_30_words):
    """Create sample script file."""
    script_path = tmp_path / "script.txt"
    script_path.write_text(sample_script_30_words, encoding="utf-8")
    return script_path


class TestForceAlignerInitialization:
    """Test ForceAligner initialization."""

    def test_init_with_default_config(self, sample_config):
        """Test initialization with default configuration."""
        aligner = ForceAligner(sample_config)

        assert aligner.config == sample_config
        assert aligner.model_name == "base"
        assert aligner.language == "en"

    def test_init_with_custom_temp_dir(self, sample_config, tmp_path):
        """Test initialization with custom temp directory."""
        custom_temp = tmp_path / "custom_temp"
        aligner = ForceAligner(sample_config, temp_dir=custom_temp)

        assert aligner.temp_dir == custom_temp

    def test_init_with_missing_alignment_config(self):
        """Test initialization when alignment config is missing."""
        from src.config import BrandConfig, CaptionConfig, BRollConfig, AudioConfig, ExportConfig

        config = Config(
            brand=BrandConfig(name="Test"),
            captions=CaptionConfig(),
            broll=BRollConfig(),
            audio=AudioConfig(),
            export=ExportConfig(),
        )
        aligner = ForceAligner(config)

        # Should use defaults
        assert aligner.model_name == "base"
        assert aligner.language == "en"


class TestForceAlignerProcess:
    """Test ForceAligner.process() method."""

    @patch("forcealign.ForceAlign")
    def test_normal_alignment_30_words(
        self,
        mock_forcealign_class,
        sample_config,
        sample_audio_path,
        sample_script_path,
        temp_output,
    ):
        """Test normal alignment with 30-word script."""
        # Setup mock ForceAlign
        mock_aligner = MagicMock()
        mock_forcealign_class.return_value = mock_aligner

        # Create mock aligned words (all 30 words aligned)
        words = [
            "this", "is", "a", "sample", "script", "for", "testing", "forced",
            "alignment", "it", "contains", "exactly", "thirty", "words",
            "including", "punctuation", "marks", "apostrophes", "like", "don't",
            "and", "hyphens", "in", "ai-powered", "technology",
        ]

        mock_words = []
        for i, word in enumerate(words):
            start = i * 0.5
            end = start + 0.4
            mock_words.append(MockWordObj(word, start, end))

        mock_aligner.inference.return_value = mock_words

        # Run alignment
        aligner = ForceAligner(sample_config)
        output_path = temp_output / "alignment.json"

        result = aligner.process(
            input_path=sample_audio_path,
            output_path=output_path,
            script_path=sample_script_path,
        )

        # Verify result
        assert result.success is True
        assert result.output_path == output_path
        assert output_path.exists()

        # Load and verify JSON output
        with open(output_path, "r", encoding="utf-8") as f:
            output_data = json.load(f)

        assert "words" in output_data
        assert "coverage" in output_data
        assert "word_count" in output_data
        assert len(output_data["words"]) == len(mock_words)
        assert output_data["coverage"] >= 0.8  # Should have good coverage

        # Verify word format
        for word_data in output_data["words"]:
            assert "word" in word_data
            assert "start" in word_data
            assert "end" in word_data
            assert isinstance(word_data["start"], (int, float))
            assert isinstance(word_data["end"], (int, float))
            assert word_data["end"] > word_data["start"]

    @patch("forcealign.ForceAlign")
    def test_punctuation_removal_and_restoration(
        self,
        mock_forcealign_class,
        sample_config,
        sample_audio_path,
        tmp_path,
        temp_output,
    ):
        """Test that punctuation is removed for alignment but restored in output."""
        # Create script with heavy punctuation
        script_text = "Hello, World! Don't forget: AI-powered tech (amazing) [works]."
        script_path = tmp_path / "script.txt"
        script_path.write_text(script_text, encoding="utf-8")

        # Setup mock - aligned words should be lowercase without punctuation
        mock_aligner = MagicMock()
        mock_forcealign_class.return_value = mock_aligner

        mock_words = [
            MockWordObj("hello", 0.0, 0.5),
            MockWordObj("world", 0.5, 1.0),
            MockWordObj("don't", 1.0, 1.5),
            MockWordObj("forget", 1.5, 2.0),
            MockWordObj("ai-powered", 2.0, 2.5),
            MockWordObj("tech", 2.5, 3.0),
            MockWordObj("amazing", 3.0, 3.5),
            MockWordObj("works", 3.5, 4.0),
        ]
        mock_aligner.inference.return_value = mock_words

        # Run alignment
        aligner = ForceAligner(sample_config)
        output_path = temp_output / "alignment.json"

        result = aligner.process(
            input_path=sample_audio_path,
            output_path=output_path,
            script_path=script_path,
        )

        # Load output
        with open(output_path, "r", encoding="utf-8") as f:
            output_data = json.load(f)

        # Verify capitalization is restored
        words_output = [w["word"] for w in output_data["words"]]
        assert "Hello" in words_output  # Capitalized
        assert "World" in words_output  # Capitalized
        assert "don't" in words_output or "Don't" in words_output  # Apostrophe preserved
        assert any("AI-powered" in w or "ai-powered" in w for w in words_output)  # Hyphen preserved

    @patch("forcealign.ForceAlign")
    def test_alignment_failure_low_coverage(
        self,
        mock_forcealign_class,
        sample_config,
        sample_audio_path,
        sample_script_path,
        temp_output,
    ):
        """Test alignment failure when coverage is too low."""
        # Setup mock with poor alignment (only 30% of words aligned)
        mock_aligner = MagicMock()
        mock_forcealign_class.return_value = mock_aligner

        # Only align 3 words out of ~30 expected
        mock_words = [
            MockWordObj("this", 0.0, 0.5),
            MockWordObj("is", 0.5, 1.0),
            MockWordObj("sample", 1.0, 1.5),
        ]
        mock_aligner.inference.return_value = mock_words

        # Run alignment with default min_coverage=0.5 (50%)
        aligner = ForceAligner(sample_config)
        output_path = temp_output / "alignment.json"

        # Should raise AlignmentError due to low coverage
        with pytest.raises(AlignmentError) as exc_info:
            aligner.process(
                input_path=sample_audio_path,
                output_path=output_path,
                script_path=sample_script_path,
            )

        assert "coverage too low" in str(exc_info.value).lower()

    @patch("forcealign.ForceAlign")
    def test_coverage_warning_threshold(
        self,
        mock_forcealign_class,
        sample_config,
        sample_audio_path,
        sample_script_path,
        temp_output,
        caplog,
    ):
        """Test warning when coverage is between 50-80%."""
        import logging
        caplog.set_level(logging.WARNING)

        # Setup mock with 70% coverage (above error threshold, below warning)
        mock_aligner = MagicMock()
        mock_forcealign_class.return_value = mock_aligner

        # Align ~17 words out of 25 expected (68% coverage)
        words = ["word"] * 17
        mock_words = []
        for i, word in enumerate(words):
            mock_words.append(MockWordObj(word, i * 0.5, (i + 1) * 0.5 - 0.1))

        mock_aligner.inference.return_value = mock_words

        # Run alignment
        aligner = ForceAligner(sample_config)
        output_path = temp_output / "alignment.json"

        result = aligner.process(
            input_path=sample_audio_path,
            output_path=output_path,
            script_path=sample_script_path,
        )

        # Should succeed but log warning
        assert result.success is True
        assert any("low alignment coverage" in record.message.lower() for record in caplog.records)

    @patch("forcealign.ForceAlign")
    def test_custom_min_coverage_threshold(
        self,
        mock_forcealign_class,
        sample_config,
        sample_audio_path,
        sample_script_path,
        temp_output,
    ):
        """Test custom minimum coverage threshold."""
        # Setup mock with 60% coverage
        mock_aligner = MagicMock()
        mock_forcealign_class.return_value = mock_aligner

        mock_words = [MockWordObj(f"word{i}", i * 0.5, (i + 1) * 0.5 - 0.1) for i in range(15)]
        mock_aligner.inference.return_value = mock_words

        aligner = ForceAligner(sample_config)
        output_path = temp_output / "alignment.json"

        # Should succeed with min_coverage=0.3 (30%)
        result = aligner.process(
            input_path=sample_audio_path,
            output_path=output_path,
            script_path=sample_script_path,
            min_coverage=0.3,
        )
        assert result.success is True

        # Should fail with min_coverage=0.9 (90%)
        with pytest.raises(AlignmentError):
            aligner.process(
                input_path=sample_audio_path,
                output_path=temp_output / "alignment2.json",
                script_path=sample_script_path,
                min_coverage=0.9,
            )


class TestGapSmoothing:
    """Test gap smoothing functionality."""

    @patch("forcealign.ForceAlign")
    def test_gap_smoothing_enabled(
        self,
        mock_forcealign_class,
        sample_config,
        sample_audio_path,
        sample_script_path,
        temp_output,
    ):
        """Test that small gaps (<50ms) are smoothed."""
        # Create words with small gaps
        mock_aligner = MagicMock()
        mock_forcealign_class.return_value = mock_aligner

        mock_words = [
            MockWordObj("hello", 0.0, 0.5),
            MockWordObj("world", 0.52, 1.0),  # 20ms gap
            MockWordObj("test", 1.03, 1.5),   # 30ms gap
        ]
        mock_aligner.inference.return_value = mock_words

        # Run alignment with smoothing enabled (default)
        aligner = ForceAligner(sample_config)
        output_path = temp_output / "alignment.json"

        result = aligner.process(
            input_path=sample_audio_path,
            output_path=output_path,
            script_path=sample_script_path,
            smooth_gaps=True,
            min_coverage=0.0,  # Allow low coverage for this test
        )

        # Load output
        with open(output_path, "r", encoding="utf-8") as f:
            output_data = json.load(f)

        words = output_data["words"]

        # Verify gaps are smoothed (words touch)
        assert words[0]["end"] == words[1]["start"]  # No gap
        assert words[1]["end"] == words[2]["start"]  # No gap

    @patch("forcealign.ForceAlign")
    def test_gap_smoothing_disabled(
        self,
        mock_forcealign_class,
        sample_config,
        sample_audio_path,
        sample_script_path,
        temp_output,
    ):
        """Test that gaps are preserved when smoothing is disabled."""
        # Create words with small gaps
        mock_aligner = MagicMock()
        mock_forcealign_class.return_value = mock_aligner

        mock_words = [
            MockWordObj("hello", 0.0, 0.5),
            MockWordObj("world", 0.52, 1.0),  # 20ms gap
        ]
        mock_aligner.inference.return_value = mock_words

        # Run alignment with smoothing disabled
        aligner = ForceAligner(sample_config)
        output_path = temp_output / "alignment.json"

        result = aligner.process(
            input_path=sample_audio_path,
            output_path=output_path,
            script_path=sample_script_path,
            smooth_gaps=False,
            min_coverage=0.0,  # Allow low coverage for this test
        )

        # Load output
        with open(output_path, "r", encoding="utf-8") as f:
            output_data = json.load(f)

        words = output_data["words"]

        # Verify gap is preserved
        assert words[0]["end"] < words[1]["start"]  # Gap exists


class TestTimingValidation:
    """Test timing validation functionality."""

    @patch("forcealign.ForceAlign")
    def test_overlapping_timestamps_warning(
        self,
        mock_forcealign_class,
        sample_config,
        sample_audio_path,
        sample_script_path,
        temp_output,
        caplog,
    ):
        """Test warning for overlapping word timestamps."""
        import logging
        caplog.set_level(logging.WARNING)

        # Create words with overlap
        mock_aligner = MagicMock()
        mock_forcealign_class.return_value = mock_aligner

        mock_words = [
            MockWordObj("hello", 0.0, 0.6),
            MockWordObj("world", 0.5, 1.0),  # Overlaps by 0.1s
        ]
        mock_aligner.inference.return_value = mock_words

        # Run alignment
        aligner = ForceAligner(sample_config)
        output_path = temp_output / "alignment.json"

        result = aligner.process(
            input_path=sample_audio_path,
            output_path=output_path,
            script_path=sample_script_path,
            smooth_gaps=False,  # Disable smoothing to preserve overlap
            min_coverage=0.0,  # Allow low coverage for this test
        )

        # Should succeed but log warning
        assert result.success is True
        assert any("overlap" in record.message.lower() for record in caplog.records)

    @patch("forcealign.ForceAlign")
    def test_large_gap_warning(
        self,
        mock_forcealign_class,
        sample_config,
        sample_audio_path,
        sample_script_path,
        temp_output,
        caplog,
    ):
        """Test warning for large gaps (>2s) between words."""
        import logging
        caplog.set_level(logging.WARNING)

        # Create words with large gap
        mock_aligner = MagicMock()
        mock_forcealign_class.return_value = mock_aligner

        mock_words = [
            MockWordObj("hello", 0.0, 0.5),
            MockWordObj("world", 3.0, 3.5),  # 2.5s gap
        ]
        mock_aligner.inference.return_value = mock_words

        # Run alignment
        aligner = ForceAligner(sample_config)
        output_path = temp_output / "alignment.json"

        result = aligner.process(
            input_path=sample_audio_path,
            output_path=output_path,
            script_path=sample_script_path,
            min_coverage=0.0,  # Allow low coverage for this test
        )

        # Should succeed but log warning
        assert result.success is True
        assert any("large gap" in record.message.lower() for record in caplog.records)

    @patch("forcealign.ForceAlign")
    def test_negative_duration_warning(
        self,
        mock_forcealign_class,
        sample_config,
        sample_audio_path,
        sample_script_path,
        temp_output,
        caplog,
    ):
        """Test warning for negative word durations."""
        import logging
        caplog.set_level(logging.WARNING)

        # Create word with negative duration (end < start)
        mock_aligner = MagicMock()
        mock_forcealign_class.return_value = mock_aligner

        mock_words = [
            MockWordObj("hello", 1.0, 0.5),  # Negative duration
        ]
        mock_aligner.inference.return_value = mock_words

        # Run alignment
        aligner = ForceAligner(sample_config)
        output_path = temp_output / "alignment.json"

        result = aligner.process(
            input_path=sample_audio_path,
            output_path=output_path,
            script_path=sample_script_path,
            min_coverage=0.0,  # Allow low coverage for this test
        )

        # Should succeed but log warning
        assert result.success is True
        assert any("invalid duration" in record.message.lower() for record in caplog.records)


class TestValidation:
    """Test input validation."""

    def test_validate_missing_audio_file(self, sample_config, tmp_path):
        """Test validation fails for missing audio file."""
        aligner = ForceAligner(sample_config)

        audio_path = tmp_path / "missing.wav"
        script_path = tmp_path / "script.txt"
        script_path.write_text("Test script", encoding="utf-8")

        errors = aligner.validate(audio_path, script_path)

        assert len(errors) > 0
        assert any("not found" in err.lower() for err in errors)

    def test_validate_wrong_audio_format(self, sample_config, tmp_path):
        """Test validation fails for non-WAV audio."""
        aligner = ForceAligner(sample_config)

        audio_path = tmp_path / "audio.mp3"
        audio_path.write_bytes(b"FAKE_MP3")
        script_path = tmp_path / "script.txt"
        script_path.write_text("Test script", encoding="utf-8")

        errors = aligner.validate(audio_path, script_path)

        assert len(errors) > 0
        assert any("wav" in err.lower() for err in errors)

    def test_validate_empty_audio_file(self, sample_config, tmp_path):
        """Test validation fails for empty audio file."""
        aligner = ForceAligner(sample_config)

        audio_path = tmp_path / "audio.wav"
        audio_path.write_bytes(b"")  # Empty file
        script_path = tmp_path / "script.txt"
        script_path.write_text("Test script", encoding="utf-8")

        errors = aligner.validate(audio_path, script_path)

        assert len(errors) > 0
        assert any("empty" in err.lower() for err in errors)

    def test_validate_missing_script_file(self, sample_config, tmp_path):
        """Test validation fails for missing script file."""
        aligner = ForceAligner(sample_config)

        audio_path = tmp_path / "audio.wav"
        audio_path.write_bytes(b"FAKE_WAV")
        script_path = tmp_path / "missing.txt"

        errors = aligner.validate(audio_path, script_path)

        assert len(errors) > 0
        assert any("not found" in err.lower() for err in errors)

    def test_validate_empty_script_file(self, sample_config, tmp_path):
        """Test validation fails for empty script file."""
        aligner = ForceAligner(sample_config)

        audio_path = tmp_path / "audio.wav"
        audio_path.write_bytes(b"FAKE_WAV")
        script_path = tmp_path / "script.txt"
        script_path.write_text("", encoding="utf-8")  # Empty script

        errors = aligner.validate(audio_path, script_path)

        assert len(errors) > 0
        assert any("empty" in err.lower() for err in errors)

    def test_validate_script_too_short(self, sample_config, tmp_path):
        """Test validation fails for script with <5 words."""
        aligner = ForceAligner(sample_config)

        audio_path = tmp_path / "audio.wav"
        audio_path.write_bytes(b"FAKE_WAV")
        script_path = tmp_path / "script.txt"
        script_path.write_text("Only three words", encoding="utf-8")

        errors = aligner.validate(audio_path, script_path)

        assert len(errors) > 0
        assert any("too short" in err.lower() for err in errors)

    def test_validate_valid_inputs(self, sample_config, sample_audio_path, sample_script_path):
        """Test validation passes for valid inputs."""
        aligner = ForceAligner(sample_config)

        errors = aligner.validate(sample_audio_path, sample_script_path)

        assert len(errors) == 0


class TestErrorHandling:
    """Test error handling in alignment process."""

    def test_forcealign_import_error(
        self,
        sample_config,
        sample_audio_path,
        sample_script_path,
        temp_output,
    ):
        """Test graceful error when forcealign is not installed."""
        import sys

        # Temporarily remove forcealign from sys.modules if it exists
        forcealign_backup = sys.modules.get('forcealign')
        if 'forcealign' in sys.modules:
            del sys.modules['forcealign']

        try:
            with patch.dict('sys.modules', {'forcealign': None}):
                aligner = ForceAligner(sample_config)
                output_path = temp_output / "alignment.json"

                with pytest.raises(RuntimeError) as exc_info:
                    aligner.process(
                        input_path=sample_audio_path,
                        output_path=output_path,
                        script_path=sample_script_path,
                    )

                assert "forcealign library not installed" in str(exc_info.value)
        finally:
            # Restore forcealign if it was there
            if forcealign_backup is not None:
                sys.modules['forcealign'] = forcealign_backup

    def test_invalid_script_format(
        self,
        sample_config,
        sample_audio_path,
        tmp_path,
        temp_output,
    ):
        """Test error when script format is invalid."""
        # Create script with only punctuation
        script_path = tmp_path / "bad_script.txt"
        script_path.write_text("!!! ??? ...", encoding="utf-8")

        aligner = ForceAligner(sample_config)
        output_path = temp_output / "alignment.json"

        with pytest.raises(RuntimeError) as exc_info:
            aligner.process(
                input_path=sample_audio_path,
                output_path=output_path,
                script_path=script_path,
            )

        # The ValueError is wrapped in RuntimeError
        assert "invalid script format" in str(exc_info.value).lower() or "script contains no words" in str(exc_info.value).lower()

    @patch("forcealign.ForceAlign")
    def test_forcealign_inference_failure(
        self,
        mock_forcealign_class,
        sample_config,
        sample_audio_path,
        sample_script_path,
        temp_output,
    ):
        """Test error handling when ForceAlign.inference() fails."""
        # Setup mock to raise exception
        mock_aligner = MagicMock()
        mock_forcealign_class.return_value = mock_aligner
        mock_aligner.inference.side_effect = Exception("Alignment model error")

        aligner = ForceAligner(sample_config)
        output_path = temp_output / "alignment.json"

        with pytest.raises(RuntimeError) as exc_info:
            aligner.process(
                input_path=sample_audio_path,
                output_path=output_path,
                script_path=sample_script_path,
            )

        assert "force alignment failed" in str(exc_info.value).lower()


class TestJSONOutput:
    """Test JSON output format."""

    @patch("forcealign.ForceAlign")
    def test_json_output_format(
        self,
        mock_forcealign_class,
        sample_config,
        sample_audio_path,
        sample_script_path,
        temp_output,
    ):
        """Test that JSON output has correct format."""
        # Setup mock
        mock_aligner = MagicMock()
        mock_forcealign_class.return_value = mock_aligner
        mock_aligner.inference.return_value = [
            MockWordObj("hello", 0.0, 0.5),
            MockWordObj("world", 0.5, 1.0),
        ]

        # Run alignment
        aligner = ForceAligner(sample_config)
        output_path = temp_output / "alignment.json"

        result = aligner.process(
            input_path=sample_audio_path,
            output_path=output_path,
            script_path=sample_script_path,
            min_coverage=0.0,  # Allow low coverage for this test
        )

        # Verify file exists and is valid JSON
        assert output_path.exists()

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Verify required fields
        assert "words" in data
        assert "coverage" in data
        assert "word_count" in data
        assert "expected_words" in data
        assert "audio_file" in data
        assert "script_file" in data

        # Verify types
        assert isinstance(data["words"], list)
        assert isinstance(data["coverage"], (int, float))
        assert isinstance(data["word_count"], int)
        assert isinstance(data["expected_words"], int)

        # Verify word format
        for word in data["words"]:
            assert "word" in word
            assert "start" in word
            assert "end" in word
            assert isinstance(word["word"], str)
            assert isinstance(word["start"], (int, float))
            assert isinstance(word["end"], (int, float))

    @patch("forcealign.ForceAlign")
    def test_json_output_utf8_encoding(
        self,
        mock_forcealign_class,
        sample_config,
        sample_audio_path,
        tmp_path,
        temp_output,
    ):
        """Test that JSON output handles UTF-8 characters correctly."""
        # Create script with UTF-8 characters (need at least 5 words)
        script_path = tmp_path / "script.txt"
        script_path.write_text("Bonjour café résumé naïve merci beaucoup", encoding="utf-8")

        # Setup mock
        mock_aligner = MagicMock()
        mock_forcealign_class.return_value = mock_aligner
        mock_aligner.inference.return_value = [
            MockWordObj("bonjour", 0.0, 0.5),
            MockWordObj("café", 0.5, 1.0),
            MockWordObj("résumé", 1.0, 1.5),
            MockWordObj("naïve", 1.5, 2.0),
            MockWordObj("merci", 2.0, 2.5),
            MockWordObj("beaucoup", 2.5, 3.0),
        ]

        # Run alignment
        aligner = ForceAligner(sample_config)
        output_path = temp_output / "alignment.json"

        result = aligner.process(
            input_path=sample_audio_path,
            output_path=output_path,
            script_path=script_path,
            min_coverage=0.0,  # Allow low coverage for this test
        )

        # Verify UTF-8 characters are preserved
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        words = [w["word"] for w in data["words"]]
        # Note: capitalization should be restored from original
        assert any("café" in w.lower() for w in words)
        assert any("résumé" in w.lower() for w in words)


class TestMetadata:
    """Test metadata in ProcessorResult."""

    @patch("forcealign.ForceAlign")
    def test_metadata_fields(
        self,
        mock_forcealign_class,
        sample_config,
        sample_audio_path,
        sample_script_path,
        temp_output,
    ):
        """Test that result metadata contains expected fields."""
        # Setup mock
        mock_aligner = MagicMock()
        mock_forcealign_class.return_value = mock_aligner
        mock_aligner.inference.return_value = [
            MockWordObj("hello", 0.0, 0.5),
            MockWordObj("world", 0.5, 1.0),
        ]

        # Run alignment
        aligner = ForceAligner(sample_config)
        output_path = temp_output / "alignment.json"

        result = aligner.process(
            input_path=sample_audio_path,
            output_path=output_path,
            script_path=sample_script_path,
            min_coverage=0.0,  # Allow low coverage for this test
        )

        # Verify metadata
        assert "word_count" in result.metadata
        assert "expected_words" in result.metadata
        assert "coverage" in result.metadata
        assert "processing_time" in result.metadata
        assert "smoothed" in result.metadata

        assert result.metadata["word_count"] == 2
        assert result.metadata["coverage"] >= 0.0  # Coverage can be 0 with min_coverage=0.0
        assert result.metadata["processing_time"] >= 0
        assert isinstance(result.metadata["smoothed"], bool)
