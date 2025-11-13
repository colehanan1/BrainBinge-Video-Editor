"""
Unit Tests for Video Composer Module

Tests video composition with FFmpeg filter graphs (mocked for speed).
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.config import AudioConfig, BRollConfig, BrandConfig, CaptionConfig, Config, ExportConfig
from src.modules.composer import VideoComposer, CompositionError


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
def sample_video_file(tmp_path):
    """Create a sample video file (empty placeholder)."""
    video_path = tmp_path / "main.mp4"
    video_path.write_bytes(b"fake video content")
    return video_path


@pytest.fixture
def sample_captions_file(tmp_path):
    """Create a sample ASS captions file."""
    ass_content = """[Script Info]
Title: Test Captions

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,28,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,0,2,10,10,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:00.50,Default,,0,0,0,,{\\be1}Test
"""
    ass_path = tmp_path / "captions.ass"
    ass_path.write_text(ass_content, encoding="utf-8")
    return ass_path


@pytest.fixture
def sample_broll_clips(tmp_path):
    """Create sample B-roll clip files."""
    clips = []
    for i in range(2):
        clip_path = tmp_path / f"broll_{i}.mp4"
        clip_path.write_bytes(b"fake broll content")
        clips.append({
            "path": clip_path,
            "start_time": i * 10.0,
            "end_time": (i * 10.0) + 5.0,
            "type": "pip" if i == 0 else "fullframe"
        })
    return clips


@pytest.fixture
def temp_output(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


class TestVideoComposerInit:
    """Test VideoComposer initialization."""

    def test_init_with_defaults(self, sample_config):
        """Test initialization with default config."""
        composer = VideoComposer(sample_config)

        assert composer.brand_name == "Test Brand"
        assert composer.video_width == 1280
        assert composer.video_height == 720
        assert composer.pip_enabled is True
        assert composer.pip_width == 400
        assert composer.pip_height == 300
        assert composer.fade_duration == 0.5
        assert composer.ducking_volume == 0.5

    def test_video_dimensions(self, sample_config):
        """Test default video dimensions."""
        composer = VideoComposer(sample_config)

        assert composer.video_width == 1280
        assert composer.video_height == 720


class TestValidation:
    """Test input validation."""

    def test_validate_main_video_exists(self, sample_config, sample_video_file):
        """Test validation passes for existing video."""
        composer = VideoComposer(sample_config)
        errors = composer.validate(sample_video_file)

        assert len(errors) == 0

    def test_validate_missing_video(self, sample_config, tmp_path):
        """Test validation fails for missing video."""
        composer = VideoComposer(sample_config)
        missing_file = tmp_path / "nonexistent.mp4"

        errors = composer.validate(missing_file)

        assert len(errors) > 0
        assert any("not found" in e.lower() for e in errors)

    def test_validate_empty_video(self, sample_config, tmp_path):
        """Test validation fails for empty video."""
        composer = VideoComposer(sample_config)
        empty_file = tmp_path / "empty.mp4"
        empty_file.write_bytes(b"")

        errors = composer.validate(empty_file)

        assert len(errors) > 0
        assert any("empty" in e.lower() for e in errors)

    def test_validate_captions_optional(self, sample_config, sample_video_file):
        """Test captions are optional."""
        composer = VideoComposer(sample_config)
        errors = composer.validate(sample_video_file, captions_path=None)

        assert len(errors) == 0

    def test_validate_missing_captions(self, sample_config, sample_video_file, tmp_path):
        """Test validation fails for missing captions file."""
        composer = VideoComposer(sample_config)
        missing_captions = tmp_path / "nonexistent.ass"

        errors = composer.validate(sample_video_file, captions_path=missing_captions)

        assert len(errors) > 0
        assert any("captions" in e.lower() and "not found" in e.lower() for e in errors)

    def test_validate_wrong_caption_format(self, sample_config, sample_video_file, tmp_path):
        """Test validation fails for non-ASS caption format."""
        composer = VideoComposer(sample_config)
        wrong_format = tmp_path / "captions.srt"
        wrong_format.write_text("fake srt", encoding="utf-8")

        errors = composer.validate(sample_video_file, captions_path=wrong_format)

        assert len(errors) > 0
        assert any("ass format" in e.lower() for e in errors)

    def test_validate_broll_clips(self, sample_config, sample_video_file, tmp_path):
        """Test validation of B-roll clips."""
        composer = VideoComposer(sample_config)

        # Missing B-roll file
        broll_clips = [{
            "path": tmp_path / "nonexistent.mp4",
            "start_time": 5.0,
            "end_time": 10.0,
            "type": "pip"
        }]

        errors = composer.validate(sample_video_file, broll_clips=broll_clips)

        assert len(errors) > 0
        assert any("broll" in e.lower() and "not found" in e.lower() for e in errors)

    def test_validate_broll_missing_fields(self, sample_config, sample_video_file):
        """Test validation fails for B-roll with missing fields."""
        composer = VideoComposer(sample_config)

        # Missing timing fields
        broll_clips = [{
            "path": sample_video_file,
            # Missing start_time and end_time
            "type": "pip"
        }]

        errors = composer.validate(sample_video_file, broll_clips=broll_clips)

        assert len(errors) > 0
        assert any("missing timing" in e.lower() for e in errors)


@patch('ffmpeg.run')
@patch('ffmpeg.probe')
class TestComposition:
    """Test video composition (with mocked FFmpeg)."""

    def test_basic_composition(
        self,
        mock_probe,
        mock_run,
        sample_config,
        sample_video_file,
        temp_output
    ):
        """Test basic composition without captions or B-roll."""
        # Mock ffmpeg.probe to return video info
        mock_probe.return_value = {
            'format': {'duration': '30.0'},
            'streams': [{'codec_type': 'video'}]
        }

        composer = VideoComposer(sample_config)
        output_path = temp_output / "composed.mp4"

        result = composer.process(sample_video_file, output_path)

        assert result.success is True
        assert result.metadata["video_resolution"] == "1280×720"
        assert result.metadata["captions_enabled"] is False
        assert result.metadata["broll_count"] == 0
        assert mock_run.called

    def test_composition_with_captions(
        self,
        mock_probe,
        mock_run,
        sample_config,
        sample_video_file,
        sample_captions_file,
        temp_output
    ):
        """Test composition with captions."""
        mock_probe.return_value = {
            'format': {'duration': '30.0'},
            'streams': [{'codec_type': 'video'}]
        }

        composer = VideoComposer(sample_config)
        output_path = temp_output / "composed.mp4"

        result = composer.process(
            sample_video_file,
            output_path,
            captions_path=sample_captions_file
        )

        assert result.success is True
        assert result.metadata["captions_enabled"] is True

    def test_composition_with_broll(
        self,
        mock_probe,
        mock_run,
        sample_config,
        sample_video_file,
        sample_broll_clips,
        temp_output
    ):
        """Test composition with B-roll clips."""
        mock_probe.return_value = {
            'format': {'duration': '30.0'},
            'streams': [{'codec_type': 'video'}]
        }

        composer = VideoComposer(sample_config)
        output_path = temp_output / "composed.mp4"

        result = composer.process(
            sample_video_file,
            output_path,
            broll_clips=sample_broll_clips
        )

        assert result.success is True
        assert result.metadata["broll_count"] == 2

    def test_composition_full_pipeline(
        self,
        mock_probe,
        mock_run,
        sample_config,
        sample_video_file,
        sample_captions_file,
        sample_broll_clips,
        temp_output
    ):
        """Test full composition with all features."""
        mock_probe.return_value = {
            'format': {'duration': '30.0'},
            'streams': [{'codec_type': 'video'}]
        }

        composer = VideoComposer(sample_config)
        output_path = temp_output / "composed.mp4"

        result = composer.process(
            sample_video_file,
            output_path,
            captions_path=sample_captions_file,
            broll_clips=sample_broll_clips,
            header_text="Custom Header"
        )

        assert result.success is True
        assert result.metadata["header_text"] == "Custom Header"
        assert result.metadata["captions_enabled"] is True
        assert result.metadata["broll_count"] == 2

    def test_custom_resolution(
        self,
        mock_probe,
        mock_run,
        sample_config,
        sample_video_file,
        temp_output
    ):
        """Test composition with custom resolution."""
        mock_probe.return_value = {
            'format': {'duration': '30.0'},
            'streams': [{'codec_type': 'video'}]
        }

        composer = VideoComposer(sample_config)
        output_path = temp_output / "composed.mp4"

        result = composer.process(
            sample_video_file,
            output_path,
            video_width=1920,
            video_height=1080
        )

        assert result.success is True
        assert result.metadata["video_resolution"] == "1920×1080"


class TestFilterMethods:
    """Test individual filter building methods."""

    def test_add_header_overlay(self, sample_config):
        """Test header overlay creation."""
        composer = VideoComposer(sample_config)

        # Create mock stream
        mock_stream = Mock()
        mock_stream.drawtext = Mock(return_value=mock_stream)

        result = composer._add_header_overlay(
            mock_stream,
            "Test Header",
            1280
        )

        # Verify drawtext was called with correct parameters
        mock_stream.drawtext.assert_called_once()
        call_kwargs = mock_stream.drawtext.call_args[1]

        assert call_kwargs['text'] == "Test Header"
        assert call_kwargs['fontsize'] == 48
        assert call_kwargs['fontcolor'] == 'white'
        assert call_kwargs['box'] == 1

    def test_burn_captions(self, sample_config, sample_captions_file):
        """Test caption burning."""
        composer = VideoComposer(sample_config)

        # Create mock stream
        mock_stream = Mock()
        mock_stream.filter = Mock(return_value=mock_stream)

        result = composer._burn_captions(mock_stream, sample_captions_file)

        # Verify subtitles filter was called
        mock_stream.filter.assert_called_once()
        assert mock_stream.filter.call_args[0][0] == 'subtitles'

    def test_apply_audio_ducking(self, sample_config):
        """Test audio ducking application."""
        composer = VideoComposer(sample_config)

        # Create mock stream
        mock_stream = Mock()
        mock_stream.filter = Mock(return_value=mock_stream)

        intervals = [(5.0, 10.0), (20.0, 25.0)]
        result = composer._apply_audio_ducking(mock_stream, intervals)

        # Verify volume filter was called
        mock_stream.filter.assert_called_once()
        assert mock_stream.filter.call_args[0][0] == 'volume'

        # Check filter expression contains ducking logic
        filter_expr = mock_stream.filter.call_args[0][1]
        assert 'between(t,5.0,10.0)' in filter_expr
        assert 'between(t,20.0,25.0)' in filter_expr
        assert str(composer.ducking_volume) in filter_expr

    def test_no_ducking_without_intervals(self, sample_config):
        """Test audio ducking is skipped when no intervals."""
        composer = VideoComposer(sample_config)

        mock_stream = Mock()
        result = composer._apply_audio_ducking(mock_stream, [])

        # Should return stream unchanged
        assert result == mock_stream


class TestErrorHandling:
    """Test error handling."""

    @patch('ffmpeg.run')
    def test_ffmpeg_error(self, mock_run, sample_config, sample_video_file, temp_output):
        """Test handling of FFmpeg errors."""
        import ffmpeg

        # Mock FFmpeg error
        mock_run.side_effect = ffmpeg.Error('ffmpeg', '', b'FFmpeg error message')

        composer = VideoComposer(sample_config)
        output_path = temp_output / "composed.mp4"

        with pytest.raises(CompositionError, match="FFmpeg composition failed"):
            composer.process(sample_video_file, output_path)

    def test_validation_error(self, sample_config, tmp_path, temp_output):
        """Test composition fails on validation error."""
        composer = VideoComposer(sample_config)
        missing_video = tmp_path / "nonexistent.mp4"
        output_path = temp_output / "composed.mp4"

        with pytest.raises(CompositionError, match="Validation failed"):
            composer.process(missing_video, output_path)


class TestEstimateDuration:
    """Test duration estimation."""

    @patch('ffmpeg.probe')
    def test_estimate_basic(self, mock_probe, sample_config, sample_video_file):
        """Test basic duration estimation."""
        mock_probe.return_value = {
            'format': {'duration': '60.0'},
            'streams': [{'codec_type': 'video'}]
        }

        composer = VideoComposer(sample_config)
        estimate = composer.estimate_duration(sample_video_file)

        # Should be ~0.5x video duration for basic composition
        assert 25.0 <= estimate <= 35.0

    @patch('ffmpeg.probe')
    def test_estimate_with_broll(self, mock_probe, sample_config, sample_video_file):
        """Test duration estimation with B-roll clips."""
        mock_probe.return_value = {
            'format': {'duration': '60.0'},
            'streams': [{'codec_type': 'video'}]
        }

        composer = VideoComposer(sample_config)
        broll_clips = [{"path": "clip1.mp4"}, {"path": "clip2.mp4"}]

        estimate = composer.estimate_duration(sample_video_file, broll_clips=broll_clips)

        # Should be longer with B-roll clips
        assert estimate > 30.0

    def test_estimate_fallback(self, sample_config, tmp_path):
        """Test fallback estimation when probe fails."""
        composer = VideoComposer(sample_config)
        nonexistent = tmp_path / "nonexistent.mp4"

        estimate = composer.estimate_duration(nonexistent)

        # Should return fallback value
        assert estimate == 60.0


class TestMetadata:
    """Test metadata in ProcessorResult."""

    @patch('ffmpeg.run')
    @patch('ffmpeg.probe')
    def test_metadata_fields(
        self,
        mock_probe,
        mock_run,
        sample_config,
        sample_video_file,
        temp_output
    ):
        """Test all expected metadata fields are present."""
        mock_probe.return_value = {
            'format': {'duration': '30.0'},
            'streams': [{'codec_type': 'video'}]
        }

        composer = VideoComposer(sample_config)
        output_path = temp_output / "composed.mp4"

        result = composer.process(sample_video_file, output_path)

        assert "video_resolution" in result.metadata
        assert "header_text" in result.metadata
        assert "captions_enabled" in result.metadata
        assert "broll_count" in result.metadata
        assert "processing_time" in result.metadata

    @patch('ffmpeg.run')
    @patch('ffmpeg.probe')
    def test_metadata_values(
        self,
        mock_probe,
        mock_run,
        sample_config,
        sample_video_file,
        temp_output
    ):
        """Test metadata values are correct."""
        mock_probe.return_value = {
            'format': {'duration': '30.0'},
            'streams': [{'codec_type': 'video'}]
        }

        composer = VideoComposer(sample_config)
        output_path = temp_output / "composed.mp4"

        result = composer.process(
            sample_video_file,
            output_path,
            header_text="My Video"
        )

        assert result.metadata["video_resolution"] == "1280×720"
        assert result.metadata["header_text"] == "My Video"
        assert result.metadata["captions_enabled"] is False
        assert result.metadata["broll_count"] == 0
        assert result.metadata["processing_time"] >= 0
