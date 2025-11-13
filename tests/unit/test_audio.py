"""
Unit tests for audio extraction module (Stage 1).

Tests cover:
- Normal audio extraction
- Audio normalization
- Metadata extraction
- Sync validation
- Error handling
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import ffmpeg

from src.modules.audio import AudioExtractor
from src.config import Config, AudioConfig, NoiseReductionConfig
from src.core.processor import ProcessorResult


@pytest.fixture
def mock_config():
    """Create mock configuration for testing."""
    config = Mock(spec=Config)
    config.audio = AudioConfig(
        sample_rate=16000,
        channels=1,
        format="wav",
        normalize=True,
        target_loudness=-16,
        noise_reduction=NoiseReductionConfig(enabled=False, strength=0.5)
    )
    return config


@pytest.fixture
def audio_extractor(mock_config):
    """Create AudioExtractor instance for testing."""
    return AudioExtractor(mock_config)


@pytest.fixture
def mock_video_path(tmp_path):
    """Create a mock video file path."""
    video_file = tmp_path / "test_video.mp4"
    video_file.touch()  # Create empty file
    return video_file


@pytest.fixture
def mock_audio_path(tmp_path):
    """Create a mock audio output path."""
    return tmp_path / "output" / "test_audio.wav"


class TestAudioExtractorInit:
    """Test AudioExtractor initialization."""

    def test_init_with_config(self, mock_config):
        """Test extractor initializes with correct config values."""
        extractor = AudioExtractor(mock_config)

        assert extractor.sample_rate == 16000
        assert extractor.channels == 1
        assert extractor.normalize is True
        assert extractor.target_loudness == -16

    def test_init_with_temp_dir(self, mock_config, tmp_path):
        """Test extractor initializes with custom temp directory."""
        temp_dir = tmp_path / "temp"
        extractor = AudioExtractor(mock_config, temp_dir=temp_dir)

        assert extractor.temp_dir == temp_dir


class TestAudioExtraction:
    """Test audio extraction functionality."""

    @patch('src.modules.audio.ffmpeg')
    def test_extract_audio_success(
        self,
        mock_ffmpeg,
        audio_extractor,
        mock_video_path,
        mock_audio_path,
        tmp_path
    ):
        """Test successful audio extraction."""
        # Mock ffmpeg operations
        mock_stream = MagicMock()
        mock_ffmpeg.input.return_value = mock_stream
        mock_stream.audio = mock_stream
        mock_ffmpeg.filter.return_value = mock_stream
        mock_ffmpeg.output.return_value = mock_stream
        mock_ffmpeg.run.return_value = None

        # Mock probe for metadata
        mock_ffmpeg.probe.side_effect = [
            # Video metadata
            {
                'format': {'duration': '60.0'},
                'streams': [
                    {
                        'codec_type': 'video',
                        'codec_name': 'h264',
                        'width': 1920,
                        'height': 1080,
                        'r_frame_rate': '30/1',
                    },
                    {
                        'codec_type': 'audio',
                        'codec_name': 'aac',
                        'sample_rate': '48000',
                        'channels': 2,
                        'bit_rate': '128000',
                    }
                ]
            },
            # Audio output metadata
            {
                'format': {'duration': '60.0', 'size': '1920000'},
                'streams': [
                    {
                        'codec_type': 'audio',
                        'codec_name': 'pcm_s16le',
                        'sample_rate': '16000',
                        'channels': 1,
                        'bits_per_sample': 16,
                    }
                ]
            },
        ]

        # Create output file to simulate successful extraction
        mock_audio_path.parent.mkdir(parents=True, exist_ok=True)
        mock_audio_path.write_bytes(b'fake audio data')

        # Execute extraction
        result = audio_extractor.process(mock_video_path, mock_audio_path)

        # Verify result
        assert result.success is True
        assert result.output_path == mock_audio_path
        assert result.metadata['sample_rate'] == 16000
        assert result.metadata['channels'] == 1
        assert result.metadata['normalized'] is True
        assert 'processing_time' in result.metadata
        assert 'sync_valid' in result.metadata

    @patch('src.modules.audio.ffmpeg')
    def test_extract_without_normalization(
        self,
        mock_ffmpeg,
        mock_video_path,
        mock_audio_path
    ):
        """Test extraction without audio normalization."""
        # Create config with normalization disabled
        config = Mock(spec=Config)
        config.audio = AudioConfig(
            sample_rate=16000,
            channels=1,
            format="wav",
            normalize=False,  # Disabled
            target_loudness=-16,
            noise_reduction=NoiseReductionConfig(enabled=False, strength=0.5)
        )
        extractor = AudioExtractor(config)

        # Mock ffmpeg operations
        mock_stream = MagicMock()
        mock_ffmpeg.input.return_value = mock_stream
        mock_stream.audio = mock_stream
        mock_ffmpeg.output.return_value = mock_stream
        mock_ffmpeg.run.return_value = None

        # Mock metadata
        mock_ffmpeg.probe.side_effect = [
            {  # Video metadata
                'format': {'duration': '30.0'},
                'streams': [
                    {'codec_type': 'video', 'codec_name': 'h264', 'width': 1920, 'height': 1080, 'r_frame_rate': '30/1'},
                    {'codec_type': 'audio', 'codec_name': 'aac', 'sample_rate': '48000', 'channels': 2, 'bit_rate': '128000'}
                ]
            },
            {  # Audio metadata
                'format': {'duration': '30.0', 'size': '960000'},
                'streams': [{'codec_type': 'audio', 'codec_name': 'pcm_s16le', 'sample_rate': '16000', 'channels': 1, 'bits_per_sample': 16}]
            },
        ]

        # Create output
        mock_audio_path.parent.mkdir(parents=True, exist_ok=True)
        mock_audio_path.write_bytes(b'audio data')

        # Execute
        result = extractor.process(mock_video_path, mock_audio_path)

        # Verify normalization was not applied
        assert result.metadata['normalized'] is False
        # Filter should not have been called
        mock_ffmpeg.filter.assert_not_called()

    @patch('src.modules.audio.ffmpeg')
    def test_extract_stereo_override(
        self,
        mock_ffmpeg,
        audio_extractor,
        mock_video_path,
        mock_audio_path
    ):
        """Test extraction with stereo override."""
        # Mock operations
        mock_stream = MagicMock()
        mock_ffmpeg.input.return_value = mock_stream
        mock_stream.audio = mock_stream
        mock_ffmpeg.filter.return_value = mock_stream
        mock_ffmpeg.output.return_value = mock_stream
        mock_ffmpeg.run.return_value = None

        # Mock metadata
        mock_ffmpeg.probe.side_effect = [
            {
                'format': {'duration': '45.0'},
                'streams': [
                    {'codec_type': 'video', 'codec_name': 'h264', 'width': 1920, 'height': 1080, 'r_frame_rate': '30/1'},
                    {'codec_type': 'audio', 'codec_name': 'aac', 'sample_rate': '48000', 'channels': 2, 'bit_rate': '128000'}
                ]
            },
            {
                'format': {'duration': '45.0', 'size': '1440000'},
                'streams': [{'codec_type': 'audio', 'codec_name': 'pcm_s16le', 'sample_rate': '16000', 'channels': 2, 'bits_per_sample': 16}]
            },
        ]

        # Create output
        mock_audio_path.parent.mkdir(parents=True, exist_ok=True)
        mock_audio_path.write_bytes(b'stereo audio')

        # Execute with stereo override
        result = audio_extractor.process(
            mock_video_path,
            mock_audio_path,
            channels=2  # Override to stereo
        )

        # Verify stereo was used
        assert result.metadata['channels'] == 2


class TestValidation:
    """Test input validation."""

    def test_validate_missing_file(self, audio_extractor, tmp_path):
        """Test validation fails for missing video file."""
        missing_file = tmp_path / "nonexistent.mp4"

        errors = audio_extractor.validate(missing_file)

        assert len(errors) > 0
        assert "not found" in errors[0].lower()

    def test_validate_empty_file(self, audio_extractor, tmp_path):
        """Test validation fails for empty video file."""
        empty_file = tmp_path / "empty.mp4"
        empty_file.touch()  # Create empty file

        errors = audio_extractor.validate(empty_file)

        assert len(errors) > 0
        assert "empty" in errors[0].lower()

    @patch('src.modules.audio.ffmpeg')
    def test_validate_no_audio_track(self, mock_ffmpeg, audio_extractor, mock_video_path):
        """Test validation fails when video has no audio track."""
        # Mock video with no audio stream
        mock_ffmpeg.probe.return_value = {
            'streams': [
                {'codec_type': 'video', 'codec_name': 'h264'}
                # No audio stream
            ]
        }

        errors = audio_extractor.validate(mock_video_path)

        assert len(errors) > 0
        assert "no audio track" in errors[0].lower()

    @patch('src.modules.audio.ffmpeg')
    def test_validate_success(self, mock_ffmpeg, audio_extractor, mock_video_path):
        """Test validation passes for valid video with audio."""
        # Mock valid video with audio
        mock_ffmpeg.probe.return_value = {
            'streams': [
                {'codec_type': 'video', 'codec_name': 'h264'},
                {'codec_type': 'audio', 'codec_name': 'aac'}
            ]
        }

        errors = audio_extractor.validate(mock_video_path)

        assert len(errors) == 0


class TestMetadataExtraction:
    """Test metadata extraction methods."""

    @patch('src.modules.audio.ffmpeg')
    def test_get_video_metadata(self, mock_ffmpeg, audio_extractor, mock_video_path):
        """Test video metadata extraction."""
        mock_ffmpeg.probe.return_value = {
            'format': {'duration': '120.5'},
            'streams': [
                {
                    'codec_type': 'video',
                    'codec_name': 'h264',
                    'width': 1280,
                    'height': 720,
                    'r_frame_rate': '30/1',
                },
                {
                    'codec_type': 'audio',
                    'codec_name': 'aac',
                    'sample_rate': '48000',
                    'channels': 2,
                    'bit_rate': '192000',
                }
            ]
        }

        metadata = audio_extractor._get_video_metadata(mock_video_path)

        assert metadata['duration'] == 120.5
        assert metadata['video_codec'] == 'h264'
        assert metadata['video_width'] == 1280
        assert metadata['video_height'] == 720
        assert metadata['video_fps'] == 30.0
        assert metadata['audio_codec'] == 'aac'
        assert metadata['audio_sample_rate'] == 48000
        assert metadata['audio_channels'] == 2

    @patch('src.modules.audio.ffmpeg')
    def test_get_audio_metadata(self, mock_ffmpeg, audio_extractor, mock_audio_path):
        """Test audio file metadata extraction."""
        mock_ffmpeg.probe.return_value = {
            'format': {'duration': '60.0', 'size': '1920000'},
            'streams': [
                {
                    'codec_type': 'audio',
                    'codec_name': 'pcm_s16le',
                    'sample_rate': '16000',
                    'channels': 1,
                    'bits_per_sample': 16,
                }
            ]
        }

        # Create dummy file
        mock_audio_path.parent.mkdir(parents=True, exist_ok=True)
        mock_audio_path.touch()

        metadata = audio_extractor._get_audio_metadata(mock_audio_path)

        assert metadata['duration'] == 60.0
        assert metadata['codec'] == 'pcm_s16le'
        assert metadata['sample_rate'] == 16000
        assert metadata['channels'] == 1
        assert metadata['bit_depth'] == 16


class TestSyncValidation:
    """Test audio/video sync validation."""

    @patch('src.modules.audio.ffmpeg')
    def test_sync_valid(self, mock_ffmpeg, audio_extractor, mock_video_path, mock_audio_path):
        """Test sync validation passes for matching durations."""
        mock_ffmpeg.probe.return_value = {
            'format': {'duration': '60.0', 'size': '1920000'},
            'streams': [
                {'codec_type': 'audio', 'codec_name': 'pcm_s16le', 'sample_rate': '16000', 'channels': 1, 'bits_per_sample': 16}
            ]
        }

        # Create dummy file
        mock_audio_path.parent.mkdir(parents=True, exist_ok=True)
        mock_audio_path.touch()

        sync_valid, drift = audio_extractor._validate_sync(
            mock_video_path,
            mock_audio_path,
            expected_duration=60.0,
            tolerance_ms=5.0
        )

        assert sync_valid is True
        assert drift == 0.0

    @patch('src.modules.audio.ffmpeg')
    def test_sync_drift_within_tolerance(self, mock_ffmpeg, audio_extractor, mock_video_path, mock_audio_path):
        """Test sync validation passes for small drift within tolerance."""
        # Audio is 60.003s (3ms drift)
        mock_ffmpeg.probe.return_value = {
            'format': {'duration': '60.003', 'size': '1920000'},
            'streams': [
                {'codec_type': 'audio', 'codec_name': 'pcm_s16le', 'sample_rate': '16000', 'channels': 1, 'bits_per_sample': 16}
            ]
        }

        mock_audio_path.parent.mkdir(parents=True, exist_ok=True)
        mock_audio_path.touch()

        sync_valid, drift = audio_extractor._validate_sync(
            mock_video_path,
            mock_audio_path,
            expected_duration=60.0,
            tolerance_ms=5.0  # 5ms tolerance
        )

        assert sync_valid is True
        assert drift < 0.005  # Less than 5ms

    @patch('src.modules.audio.ffmpeg')
    def test_sync_drift_exceeds_tolerance(self, mock_ffmpeg, audio_extractor, mock_video_path, mock_audio_path):
        """Test sync validation fails for drift exceeding tolerance."""
        # Audio is 60.050s (50ms drift)
        mock_ffmpeg.probe.return_value = {
            'format': {'duration': '60.050', 'size': '1920000'},
            'streams': [
                {'codec_type': 'audio', 'codec_name': 'pcm_s16le', 'sample_rate': '16000', 'channels': 1, 'bits_per_sample': 16}
            ]
        }

        mock_audio_path.parent.mkdir(parents=True, exist_ok=True)
        mock_audio_path.touch()

        sync_valid, drift = audio_extractor._validate_sync(
            mock_video_path,
            mock_audio_path,
            expected_duration=60.0,
            tolerance_ms=5.0  # 5ms tolerance
        )

        assert sync_valid is False
        assert drift == pytest.approx(0.050, abs=0.001)


class TestErrorHandling:
    """Test error handling."""

    @patch('src.modules.audio.ffmpeg')
    def test_ffmpeg_error(self, mock_ffmpeg, audio_extractor, mock_video_path, mock_audio_path):
        """Test handling of FFmpeg errors."""
        # Mock FFmpeg error
        mock_stream = MagicMock()
        mock_ffmpeg.input.return_value = mock_stream
        mock_stream.audio = mock_stream
        mock_ffmpeg.filter.return_value = mock_stream
        mock_ffmpeg.output.return_value = mock_stream

        error = ffmpeg.Error('ffmpeg', b'', b'FFmpeg error: invalid codec')
        mock_ffmpeg.run.side_effect = error

        # Mock metadata probe
        mock_ffmpeg.probe.return_value = {
            'format': {'duration': '60.0'},
            'streams': [
                {'codec_type': 'video', 'codec_name': 'h264', 'width': 1920, 'height': 1080, 'r_frame_rate': '30/1'},
                {'codec_type': 'audio', 'codec_name': 'aac', 'sample_rate': '48000', 'channels': 2, 'bit_rate': '128000'}
            ]
        }

        # Execution should raise RuntimeError
        with pytest.raises(RuntimeError, match="Audio extraction failed"):
            audio_extractor.process(mock_video_path, mock_audio_path)

    @patch('src.modules.audio.ffmpeg')
    def test_output_not_created(self, mock_ffmpeg, audio_extractor, mock_video_path, mock_audio_path):
        """Test error when output file is not created."""
        # Mock successful ffmpeg run but no output file
        mock_stream = MagicMock()
        mock_ffmpeg.input.return_value = mock_stream
        mock_stream.audio = mock_stream
        mock_ffmpeg.filter.return_value = mock_stream
        mock_ffmpeg.output.return_value = mock_stream
        mock_ffmpeg.run.return_value = None

        # Mock metadata
        mock_ffmpeg.probe.return_value = {
            'format': {'duration': '60.0'},
            'streams': [
                {'codec_type': 'video', 'codec_name': 'h264', 'width': 1920, 'height': 1080, 'r_frame_rate': '30/1'},
                {'codec_type': 'audio', 'codec_name': 'aac', 'sample_rate': '48000', 'channels': 2, 'bit_rate': '128000'}
            ]
        }

        # Don't create output file (simulating failure)

        with pytest.raises(RuntimeError, match="not created"):
            audio_extractor.process(mock_video_path, mock_audio_path)


class TestDurationEstimation:
    """Test processing duration estimation."""

    @patch('src.modules.audio.ffmpeg')
    def test_estimate_duration_without_normalization(self, mock_ffmpeg, mock_video_path):
        """Test duration estimation for extraction without normalization."""
        # Create config with normalization disabled
        config = Mock(spec=Config)
        config.audio = AudioConfig(
            sample_rate=16000,
            channels=1,
            format="wav",
            normalize=False,  # Disabled
            target_loudness=-16,
            noise_reduction=NoiseReductionConfig(enabled=False, strength=0.5)
        )
        extractor = AudioExtractor(config)

        mock_ffmpeg.probe.return_value = {
            'format': {'duration': '100.0'}
        }

        estimated = extractor.estimate_duration(mock_video_path)

        # Should be ~8% of video duration without normalization
        assert estimated == pytest.approx(8.0, abs=1.0)

    @patch('src.modules.audio.ffmpeg')
    def test_estimate_duration_with_normalization(self, mock_ffmpeg, audio_extractor, mock_video_path):
        """Test duration estimation for extraction with normalization."""
        mock_ffmpeg.probe.return_value = {
            'format': {'duration': '100.0'}
        }

        estimated = audio_extractor.estimate_duration(mock_video_path)

        # Should be ~12% of video duration with normalization
        assert estimated == pytest.approx(12.0, abs=1.0)

    def test_estimate_duration_fallback(self, audio_extractor, tmp_path):
        """Test duration estimation fallback for invalid files."""
        invalid_file = tmp_path / "invalid.mp4"

        estimated = audio_extractor.estimate_duration(invalid_file)

        # Should return default fallback
        assert estimated == 5.0
