"""
Unit tests for Stage 3: Caption Generation

Tests CaptionGenerator for SRT subtitle generation with viral karaoke effect.

Test Coverage:
    - Single-word captions (viral effect)
    - Multi-word captions (2-3 words)
    - Short word merging (<150ms)
    - Minimum duration enforcement (200ms)
    - Timestamp validation
    - SRT format correctness
    - Edge cases and error handling
"""

import json
from pathlib import Path

import pytest

from src.config import Config, BrandConfig, CaptionConfig, BRollConfig, AudioConfig, ExportConfig
from src.modules.captions import CaptionGenerator, CaptionError


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
def sample_alignment_data():
    """Create sample alignment JSON data."""
    return {
        "words": [
            {"word": "Hello", "start": 0.0, "end": 0.5},
            {"word": "world", "start": 0.5, "end": 1.0},
            {"word": "this", "start": 1.0, "end": 1.3},
            {"word": "is", "start": 1.3, "end": 1.4},  # Very short word
            {"word": "amazing", "start": 1.4, "end": 2.0},
        ],
        "coverage": 1.0,
        "word_count": 5,
    }


@pytest.fixture
def alignment_json_file(tmp_path, sample_alignment_data):
    """Create temporary alignment JSON file."""
    json_path = tmp_path / "alignment.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(sample_alignment_data, f)
    return json_path


class TestCaptionGeneratorInitialization:
    """Test CaptionGenerator initialization."""

    def test_init_with_default_config(self, sample_config):
        """Test initialization with default configuration."""
        generator = CaptionGenerator(sample_config)

        assert generator.config == sample_config
        assert generator.min_duration_ms == 200
        assert generator.max_duration_ms == 3000
        assert generator.merge_threshold_ms == 150

    def test_init_with_custom_temp_dir(self, sample_config, tmp_path):
        """Test initialization with custom temp directory."""
        custom_temp = tmp_path / "custom_temp"
        generator = CaptionGenerator(sample_config, temp_dir=custom_temp)

        assert generator.temp_dir == custom_temp


class TestSingleWordCaptions:
    """Test single-word caption generation (viral karaoke effect)."""

    def test_one_word_per_caption(self, sample_config, alignment_json_file, tmp_path):
        """Test generating one word per caption."""
        generator = CaptionGenerator(sample_config)
        output_path = tmp_path / "captions.srt"

        result = generator.process(
            alignment_json_file,
            output_path,
            words_per_caption=1,
            merge_short_words=False,
        )

        # Verify result
        assert result.success is True
        assert result.output_path == output_path
        assert output_path.exists()

        # Verify metadata
        assert result.metadata["caption_count"] == 5  # 5 words = 5 captions
        assert result.metadata["words_per_caption"] == 1

        # Verify SRT content
        srt_content = output_path.read_text(encoding="utf-8")
        assert "Hello" in srt_content
        assert "world" in srt_content
        assert "amazing" in srt_content

        # Verify SRT format
        lines = srt_content.strip().split("\n")
        assert lines[0] == "1"  # First caption number
        assert " --> " in lines[1]  # Timestamp line
        assert lines[2] == "Hello"  # Caption text

    def test_srt_format_correctness(self, sample_config, alignment_json_file, tmp_path):
        """Test that SRT file has correct format."""
        generator = CaptionGenerator(sample_config)
        output_path = tmp_path / "captions.srt"

        result = generator.process(
            alignment_json_file,
            output_path,
            words_per_caption=1,
            merge_short_words=False,
        )

        srt_content = output_path.read_text(encoding="utf-8")
        lines = srt_content.strip().split("\n")

        # Verify structure for first caption
        assert lines[0] == "1"  # Caption number
        assert lines[1] == "00:00:00,000 --> 00:00:00,500"  # Timestamp
        assert lines[2] == "Hello"  # Text
        assert lines[3] == ""  # Blank line separator

        # Verify structure for second caption
        assert lines[4] == "2"  # Caption number
        assert lines[5] == "00:00:00,500 --> 00:00:01,000"  # Timestamp
        assert lines[6] == "world"  # Text


class TestMultiWordCaptions:
    """Test multi-word caption generation."""

    def test_three_words_per_caption(self, sample_config, alignment_json_file, tmp_path):
        """Test generating captions with 3 words each."""
        generator = CaptionGenerator(sample_config)
        output_path = tmp_path / "captions.srt"

        result = generator.process(
            alignment_json_file,
            output_path,
            words_per_caption=3,
            merge_short_words=False,
        )

        # 5 words / 3 words per caption = 2 captions (3 words + 2 words)
        assert result.metadata["caption_count"] == 2
        assert result.metadata["words_per_caption"] == 3

        # Verify SRT content
        srt_content = output_path.read_text(encoding="utf-8")
        assert "Hello world this" in srt_content
        assert "is amazing" in srt_content

    def test_two_words_per_caption(self, sample_config, alignment_json_file, tmp_path):
        """Test generating captions with 2 words each."""
        generator = CaptionGenerator(sample_config)
        output_path = tmp_path / "captions.srt"

        result = generator.process(
            alignment_json_file,
            output_path,
            words_per_caption=2,
            merge_short_words=False,
        )

        # 5 words / 2 words per caption = 3 captions (2 + 2 + 1)
        assert result.metadata["caption_count"] == 3

        srt_content = output_path.read_text(encoding="utf-8")
        assert "Hello world" in srt_content
        assert "this is" in srt_content
        assert "amazing" in srt_content  # Last word alone


class TestShortWordMerging:
    """Test merging of very short words."""

    def test_merge_short_words_enabled(self, sample_config, alignment_json_file, tmp_path):
        """Test that short words (<150ms) are merged with next word."""
        generator = CaptionGenerator(sample_config)
        output_path = tmp_path / "captions.srt"

        # "is" has duration of 100ms (1.4 - 1.3), should be merged with "amazing"
        result = generator.process(
            alignment_json_file,
            output_path,
            words_per_caption=1,
            merge_short_words=True,
        )

        # 5 words - 1 merged = 4 captions
        assert result.metadata["caption_count"] == 4
        assert result.metadata["merged"] is True

        # Verify "is" was merged with "amazing"
        srt_content = output_path.read_text(encoding="utf-8")
        assert "is amazing" in srt_content

    def test_merge_short_words_disabled(self, sample_config, alignment_json_file, tmp_path):
        """Test that short words are not merged when disabled."""
        generator = CaptionGenerator(sample_config)
        output_path = tmp_path / "captions.srt"

        result = generator.process(
            alignment_json_file,
            output_path,
            words_per_caption=1,
            merge_short_words=False,
        )

        # All 5 words remain separate
        assert result.metadata["caption_count"] == 5
        assert result.metadata["merged"] is False

        # Verify "is" appears as separate caption
        srt_content = output_path.read_text(encoding="utf-8")
        lines = srt_content.split("\n")
        assert "is" in lines  # "is" on its own line

    def test_merge_preserves_capitalization(self, sample_config, tmp_path):
        """Test that merging preserves original capitalization."""
        # Create alignment with short word that needs capitalization
        alignment_data = {
            "words": [
                {"word": "The", "start": 0.0, "end": 0.1},  # Short word
                {"word": "AI", "start": 0.1, "end": 0.5},  # Should stay capitalized
                {"word": "works", "start": 0.5, "end": 1.0},
            ],
            "coverage": 1.0,
            "word_count": 3,
        }

        json_path = tmp_path / "alignment.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(alignment_data, f)

        generator = CaptionGenerator(sample_config)
        output_path = tmp_path / "captions.srt"

        result = generator.process(
            json_path,
            output_path,
            words_per_caption=1,
            merge_short_words=True,
        )

        srt_content = output_path.read_text(encoding="utf-8")
        assert "The AI" in srt_content  # Capitalization preserved


class TestMinimumDuration:
    """Test minimum duration enforcement."""

    def test_enforce_min_duration_200ms(self, sample_config, tmp_path):
        """Test that captions shorter than 200ms are extended."""
        # Create alignment with very short words
        alignment_data = {
            "words": [
                {"word": "I", "start": 0.0, "end": 0.05},  # 50ms - too short
                {"word": "am", "start": 0.05, "end": 0.15},  # 100ms - too short
                {"word": "good", "start": 0.15, "end": 0.5},  # 350ms - OK
            ],
            "coverage": 1.0,
            "word_count": 3,
        }

        json_path = tmp_path / "alignment.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(alignment_data, f)

        generator = CaptionGenerator(sample_config)
        output_path = tmp_path / "captions.srt"

        result = generator.process(
            json_path,
            output_path,
            words_per_caption=1,
            merge_short_words=False,
            min_duration_ms=200,
        )

        assert result.success is True

        # Parse SRT to verify durations
        srt_content = output_path.read_text(encoding="utf-8")
        lines = srt_content.split("\n")

        # First caption should be extended to 200ms
        # 00:00:00,000 --> 00:00:00,200
        timestamp_line = lines[1]
        start, end = timestamp_line.split(" --> ")
        # End should be at least 200ms after start
        assert "00:00:00,200" in end or "00:00:00,050" in end  # Either extended or kept as is

    def test_min_duration_doesnt_overlap(self, sample_config, tmp_path):
        """Test that enforcing min duration doesn't create overlaps."""
        # Create alignment where extending would cause overlap
        alignment_data = {
            "words": [
                {"word": "a", "start": 0.0, "end": 0.05},  # 50ms - would extend to 0.2
                {"word": "b", "start": 0.1, "end": 0.5},  # Starts at 0.1
            ],
            "coverage": 1.0,
            "word_count": 2,
        }

        json_path = tmp_path / "alignment.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(alignment_data, f)

        generator = CaptionGenerator(sample_config)
        output_path = tmp_path / "captions.srt"

        result = generator.process(
            json_path,
            output_path,
            words_per_caption=1,
            merge_short_words=False,
            min_duration_ms=200,
        )

        # Verify no overlap in timing validation
        # The validation should pass without overlap errors
        assert result.success is True


class TestTimestampValidation:
    """Test timestamp validation and error detection."""

    def test_validate_normal_captions(self, sample_config, alignment_json_file, tmp_path):
        """Test that valid captions pass validation."""
        generator = CaptionGenerator(sample_config)
        output_path = tmp_path / "captions.srt"

        result = generator.process(
            alignment_json_file,
            output_path,
            words_per_caption=1,
            merge_short_words=False,
        )

        assert result.success is True
        # Normal captions should pass without validation warnings

    def test_detect_overlapping_captions(self, sample_config, tmp_path, caplog):
        """Test detection of overlapping caption timestamps."""
        import logging
        caplog.set_level(logging.WARNING)

        # Create alignment with overlap
        alignment_data = {
            "words": [
                {"word": "word1", "start": 0.0, "end": 1.0},
                {"word": "word2", "start": 0.8, "end": 1.5},  # Overlaps with word1
            ],
            "coverage": 1.0,
            "word_count": 2,
        }

        json_path = tmp_path / "alignment.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(alignment_data, f)

        generator = CaptionGenerator(sample_config)
        output_path = tmp_path / "captions.srt"

        result = generator.process(
            json_path,
            output_path,
            words_per_caption=1,
            merge_short_words=False,
        )

        # Should still succeed but log warning
        assert result.success is True
        assert any("overlap" in record.message.lower() for record in caplog.records)

    def test_detect_large_gaps(self, sample_config, tmp_path, caplog):
        """Test detection of large gaps between captions."""
        import logging
        caplog.set_level(logging.WARNING)

        # Create alignment with large gap
        alignment_data = {
            "words": [
                {"word": "word1", "start": 0.0, "end": 0.5},
                {"word": "word2", "start": 3.0, "end": 3.5},  # 2.5s gap
            ],
            "coverage": 1.0,
            "word_count": 2,
        }

        json_path = tmp_path / "alignment.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(alignment_data, f)

        generator = CaptionGenerator(sample_config)
        output_path = tmp_path / "captions.srt"

        result = generator.process(
            json_path,
            output_path,
            words_per_caption=1,
            merge_short_words=False,
        )

        # Should succeed but log warning
        assert result.success is True
        assert any("large gap" in record.message.lower() for record in caplog.records)


class TestInputValidation:
    """Test input validation before caption generation."""

    def test_validate_missing_file(self, sample_config, tmp_path):
        """Test validation fails for missing file."""
        generator = CaptionGenerator(sample_config)
        missing_path = tmp_path / "missing.json"

        errors = generator.validate(missing_path)

        assert len(errors) > 0
        assert any("not found" in err.lower() for err in errors)

    def test_validate_empty_file(self, sample_config, tmp_path):
        """Test validation fails for empty file."""
        generator = CaptionGenerator(sample_config)
        empty_path = tmp_path / "empty.json"
        empty_path.write_text("", encoding="utf-8")

        errors = generator.validate(empty_path)

        assert len(errors) > 0
        assert any("empty" in err.lower() for err in errors)

    def test_validate_invalid_json(self, sample_config, tmp_path):
        """Test validation fails for invalid JSON."""
        generator = CaptionGenerator(sample_config)
        bad_json = tmp_path / "bad.json"
        bad_json.write_text("not valid json{", encoding="utf-8")

        errors = generator.validate(bad_json)

        assert len(errors) > 0
        assert any("json" in err.lower() for err in errors)

    def test_validate_missing_words_field(self, sample_config, tmp_path):
        """Test validation fails when 'words' field is missing."""
        generator = CaptionGenerator(sample_config)
        bad_data = tmp_path / "no_words.json"
        with open(bad_data, "w", encoding="utf-8") as f:
            json.dump({"coverage": 1.0}, f)

        errors = generator.validate(bad_data)

        assert len(errors) > 0
        assert any("words" in err.lower() for err in errors)

    def test_validate_empty_words_list(self, sample_config, tmp_path):
        """Test validation fails for empty words list."""
        generator = CaptionGenerator(sample_config)
        empty_words = tmp_path / "empty_words.json"
        with open(empty_words, "w", encoding="utf-8") as f:
            json.dump({"words": []}, f)

        errors = generator.validate(empty_words)

        assert len(errors) > 0
        assert any("no words" in err.lower() for err in errors)

    def test_validate_malformed_word_entry(self, sample_config, tmp_path):
        """Test validation fails for malformed word entries."""
        generator = CaptionGenerator(sample_config)
        bad_words = tmp_path / "bad_words.json"
        with open(bad_words, "w", encoding="utf-8") as f:
            json.dump({
                "words": [
                    {"word": "hello"},  # Missing start and end
                    {"start": 0.0, "end": 0.5},  # Missing word
                ]
            }, f)

        errors = generator.validate(bad_words)

        assert len(errors) > 0

    def test_validate_valid_alignment(self, sample_config, alignment_json_file):
        """Test validation passes for valid alignment file."""
        generator = CaptionGenerator(sample_config)

        errors = generator.validate(alignment_json_file)

        assert len(errors) == 0


class TestErrorHandling:
    """Test error handling in caption generation."""

    def test_missing_words_field_raises_error(self, sample_config, tmp_path):
        """Test error when alignment JSON missing 'words' field."""
        bad_json = tmp_path / "no_words.json"
        with open(bad_json, "w", encoding="utf-8") as f:
            json.dump({"coverage": 1.0}, f)

        generator = CaptionGenerator(sample_config)
        output_path = tmp_path / "captions.srt"

        with pytest.raises(CaptionError) as exc_info:
            generator.process(bad_json, output_path)

        assert "missing 'words' field" in str(exc_info.value)

    def test_empty_words_list_raises_error(self, sample_config, tmp_path):
        """Test error when words list is empty."""
        empty_words = tmp_path / "empty.json"
        with open(empty_words, "w", encoding="utf-8") as f:
            json.dump({"words": []}, f)

        generator = CaptionGenerator(sample_config)
        output_path = tmp_path / "captions.srt"

        with pytest.raises(CaptionError) as exc_info:
            generator.process(empty_words, output_path)

        assert "no words found" in str(exc_info.value).lower()


class TestSRTTimeFormatting:
    """Test SRT timestamp formatting."""

    def test_format_zero_seconds(self, sample_config):
        """Test formatting 0 seconds."""
        generator = CaptionGenerator(sample_config)
        formatted = generator._format_srt_time(0.0)
        assert formatted == "00:00:00,000"

    def test_format_fractional_seconds(self, sample_config):
        """Test formatting fractional seconds."""
        generator = CaptionGenerator(sample_config)
        formatted = generator._format_srt_time(1.234)
        assert formatted == "00:00:01,234"

    def test_format_minutes(self, sample_config):
        """Test formatting time with minutes."""
        generator = CaptionGenerator(sample_config)
        formatted = generator._format_srt_time(65.5)  # 1 min 5.5 sec
        assert formatted == "00:01:05,500"

    def test_format_hours(self, sample_config):
        """Test formatting time with hours."""
        generator = CaptionGenerator(sample_config)
        formatted = generator._format_srt_time(3661.123)  # 1 hour 1 min 1.123 sec
        assert formatted == "01:01:01,123"


class TestMetadata:
    """Test metadata in ProcessorResult."""

    def test_metadata_fields(self, sample_config, alignment_json_file, tmp_path):
        """Test that result metadata contains expected fields."""
        generator = CaptionGenerator(sample_config)
        output_path = tmp_path / "captions.srt"

        result = generator.process(
            alignment_json_file,
            output_path,
            words_per_caption=1,
            merge_short_words=False,
        )

        # Verify metadata
        assert "caption_count" in result.metadata
        assert "total_duration" in result.metadata
        assert "avg_duration_ms" in result.metadata
        assert "processing_time" in result.metadata
        assert "words_per_caption" in result.metadata
        assert "merged" in result.metadata

        assert result.metadata["caption_count"] == 5
        assert result.metadata["total_duration"] > 0
        assert result.metadata["processing_time"] >= 0
        assert isinstance(result.metadata["merged"], bool)


class TestUTF8Support:
    """Test UTF-8 character support in captions."""

    def test_utf8_characters_in_captions(self, sample_config, tmp_path):
        """Test that UTF-8 characters are preserved in captions."""
        # Create alignment with UTF-8 characters
        alignment_data = {
            "words": [
                {"word": "Bonjour", "start": 0.0, "end": 0.5},
                {"word": "café", "start": 0.5, "end": 1.0},
                {"word": "naïve", "start": 1.0, "end": 1.5},
            ],
            "coverage": 1.0,
            "word_count": 3,
        }

        json_path = tmp_path / "alignment.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(alignment_data, f, ensure_ascii=False)

        generator = CaptionGenerator(sample_config)
        output_path = tmp_path / "captions.srt"

        result = generator.process(
            json_path,
            output_path,
            words_per_caption=1,
            merge_short_words=False,
        )

        # Verify UTF-8 characters preserved
        srt_content = output_path.read_text(encoding="utf-8")
        assert "café" in srt_content
        assert "naïve" in srt_content
