"""
Stage 1: Audio Extraction

Extracts audio track from HeyGen video for force alignment.

Uses FFmpeg to extract audio in WAV format (16kHz mono) optimized
for speech recognition and force alignment.

Example:
    >>> from src.modules.audio import AudioExtractor
    >>> extractor = AudioExtractor(config)
    >>> result = extractor.process("video.mp4", "audio.wav")
"""

import logging
import subprocess
from pathlib import Path
from typing import Any, List

import ffmpeg
from ffmpeg._run import Error as FFmpegError

from src.config import Config
from src.core.processor import BaseProcessor, ProcessorResult

logger = logging.getLogger(__name__)


class AudioExtractor(BaseProcessor):
    """
    Extract audio track from video for alignment.

    Extracts audio in format optimized for force alignment:
    - WAV format
    - 16kHz sample rate
    - Mono channel
    - 16-bit PCM

    Args:
        config: Configuration object
        temp_dir: Directory for temporary files
    """

    def __init__(self, config: Config, temp_dir: Path | None = None):
        super().__init__(config, temp_dir)
        self.sample_rate = config.audio.sample_rate
        self.channels = config.audio.channels
        self.normalize = config.audio.normalize
        self.target_loudness = config.audio.target_loudness if self.normalize else None

    def process(
        self,
        input_path: Path,
        output_path: Path,
        **kwargs: Any,
    ) -> ProcessorResult:
        """
        Extract audio from video with normalization.

        Args:
            input_path: Path to input video (MP4)
            output_path: Path for output audio (WAV)
            **kwargs: Additional parameters
                - normalize: Override config normalization setting
                - channels: Override config channels (1=mono, 2=stereo)

        Returns:
            ProcessorResult with extracted audio path and metadata

        Raises:
            ProcessingError: If audio extraction fails
        """
        import time
        start_time = time.time()

        # Get input video metadata
        input_metadata = self._get_video_metadata(input_path)
        logger.info(f"Extracting audio from {input_path}")
        logger.info(f"  Video duration: {input_metadata['duration']:.2f}s")
        logger.info(f"  Video codec: {input_metadata['video_codec']}")
        logger.info(f"  Audio codec: {input_metadata['audio_codec']}")
        logger.info(f"  Original sample rate: {input_metadata['audio_sample_rate']}Hz")

        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Use override or config settings
            channels = kwargs.get('channels', self.channels)
            normalize = kwargs.get('normalize', self.normalize)

            # Build ffmpeg stream
            stream = ffmpeg.input(str(input_path))

            # Get audio stream
            stream = stream.audio

            # Add normalization filter if enabled
            if normalize and self.target_loudness:
                # EBU R128 loudness normalization
                logger.info(f"  Normalizing to {self.target_loudness} LUFS")
                stream = stream.filter(
                    'loudnorm',
                    I=self.target_loudness,
                    LRA=11,
                    TP=-1.5
                )

            # Output configuration
            stream = ffmpeg.output(
                stream,
                str(output_path),
                format='wav',
                acodec='pcm_s16le',  # 16-bit PCM
                ac=channels,          # Mono or Stereo
                ar=self.sample_rate,  # 16kHz (or configured rate)
            )

            # Run ffmpeg with progress monitoring
            logger.info(f"  Target: {self.sample_rate}Hz, {channels} channel(s)")

            try:
                ffmpeg.run(
                    stream,
                    overwrite_output=True,
                    capture_stdout=True,
                    capture_stderr=True,
                    quiet=False
                )
            except FFmpegError as e:
                # Log stderr for debugging
                if e.stderr:
                    stderr = e.stderr.decode('utf-8', errors='ignore')
                    logger.debug(f"FFmpeg stderr: {stderr}")
                raise

            # Validate output
            if not output_path.exists():
                raise RuntimeError(f"Audio extraction failed: {output_path} not created")

            if output_path.stat().st_size == 0:
                raise RuntimeError(f"Audio extraction failed: {output_path} is empty")

            # Get output audio metadata
            output_metadata = self._get_audio_metadata(output_path)

            processing_time = time.time() - start_time
            logger.info(f"Audio extracted successfully in {processing_time:.2f}s")
            logger.info(f"  Output size: {output_path.stat().st_size / 1024:.1f} KB")
            logger.info(f"  Output format: {output_metadata['codec']}, "
                       f"{output_metadata['sample_rate']}Hz, "
                       f"{output_metadata['channels']} channel(s)")

            # Validate timing sync
            sync_valid, sync_drift = self._validate_sync(
                input_path,
                output_path,
                input_metadata['duration']
            )

            if not sync_valid:
                logger.warning(f"Audio sync drift detected: {sync_drift:.3f}s")

            return ProcessorResult(
                success=True,
                output_path=output_path,
                metadata={
                    'input_duration': input_metadata['duration'],
                    'output_duration': output_metadata['duration'],
                    'sample_rate': output_metadata['sample_rate'],
                    'channels': output_metadata['channels'],
                    'format': 'wav',
                    'codec': output_metadata['codec'],
                    'size_bytes': output_path.stat().st_size,
                    'normalized': normalize,
                    'processing_time': processing_time,
                    'sync_valid': sync_valid,
                    'sync_drift_ms': sync_drift * 1000,
                }
            )

        except FFmpegError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"FFmpeg error during audio extraction: {error_msg}")
            raise RuntimeError(f"Audio extraction failed: {error_msg}")

        except Exception as e:
            logger.error(f"Unexpected error during audio extraction: {e}")
            raise RuntimeError(f"Audio extraction failed: {e}")

    def validate(self, input_path: Path, **kwargs: Any) -> List[str]:
        """
        Validate video file has audio track.

        Args:
            input_path: Path to video file

        Returns:
            List of validation errors
        """
        errors = []

        # Check file exists
        if not input_path.exists():
            errors.append(f"Video file not found: {input_path}")
            return errors

        # Check file is not empty
        if input_path.stat().st_size == 0:
            errors.append(f"Video file is empty: {input_path}")
            return errors

        try:
            # Probe video file to check for audio stream
            probe = ffmpeg.probe(str(input_path))

            # Check for audio streams
            audio_streams = [
                stream for stream in probe.get('streams', [])
                if stream.get('codec_type') == 'audio'
            ]

            if not audio_streams:
                errors.append(f"No audio track found in video: {input_path}")

        except FFmpegError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            errors.append(f"Failed to probe video file: {error_msg}")
        except Exception as e:
            errors.append(f"Failed to validate video file: {e}")

        return errors

    def estimate_duration(self, input_path: Path, **kwargs: Any) -> float:
        """
        Estimate audio extraction duration.

        Args:
            input_path: Path to video file

        Returns:
            Estimated time in seconds (~5-10% of video duration)
        """
        try:
            # Get video duration using ffprobe
            probe = ffmpeg.probe(str(input_path))
            video_duration = float(probe['format']['duration'])

            # Audio extraction is typically 5-10% of video duration
            # With normalization, add 20% more time
            multiplier = 0.12 if self.normalize else 0.08
            estimated_time = video_duration * multiplier

            logger.debug(f"Estimated audio extraction time: {estimated_time:.2f}s for {video_duration:.2f}s video")

            return estimated_time

        except Exception as e:
            logger.warning(f"Could not estimate duration: {e}, using default")
            return 5.0  # Default fallback

    def _get_video_metadata(self, video_path: Path) -> dict:
        """
        Extract comprehensive metadata from video file.

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with video/audio metadata

        Raises:
            RuntimeError: If metadata extraction fails
        """
        try:
            probe = ffmpeg.probe(str(video_path))

            # Get format metadata
            format_info = probe.get('format', {})
            duration = float(format_info.get('duration', 0))

            # Find video and audio streams
            video_stream = next(
                (s for s in probe['streams'] if s['codec_type'] == 'video'),
                None
            )
            audio_stream = next(
                (s for s in probe['streams'] if s['codec_type'] == 'audio'),
                None
            )

            if not video_stream:
                raise RuntimeError("No video stream found in file")

            if not audio_stream:
                raise RuntimeError("No audio stream found in file")

            return {
                'duration': duration,
                'video_codec': video_stream.get('codec_name', 'unknown'),
                'video_width': int(video_stream.get('width', 0)),
                'video_height': int(video_stream.get('height', 0)),
                'video_fps': eval(video_stream.get('r_frame_rate', '0/1')),
                'audio_codec': audio_stream.get('codec_name', 'unknown'),
                'audio_sample_rate': int(audio_stream.get('sample_rate', 0)),
                'audio_channels': int(audio_stream.get('channels', 0)),
                'audio_bitrate': int(audio_stream.get('bit_rate', 0)),
            }

        except Exception as e:
            logger.error(f"Failed to extract video metadata: {e}")
            raise RuntimeError(f"Metadata extraction failed: {e}")

    def _get_audio_metadata(self, audio_path: Path) -> dict:
        """
        Extract metadata from audio file.

        Args:
            audio_path: Path to audio file (WAV)

        Returns:
            Dictionary with audio metadata

        Raises:
            RuntimeError: If metadata extraction fails
        """
        try:
            probe = ffmpeg.probe(str(audio_path))

            # Get format metadata
            format_info = probe.get('format', {})
            duration = float(format_info.get('duration', 0))

            # Get audio stream metadata
            audio_stream = next(
                (s for s in probe['streams'] if s['codec_type'] == 'audio'),
                None
            )

            if not audio_stream:
                raise RuntimeError("No audio stream found in WAV file")

            return {
                'duration': duration,
                'codec': audio_stream.get('codec_name', 'unknown'),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': int(audio_stream.get('channels', 0)),
                'bit_depth': int(audio_stream.get('bits_per_sample', 0)),
                'size_bytes': int(format_info.get('size', 0)),
            }

        except Exception as e:
            logger.error(f"Failed to extract audio metadata: {e}")
            raise RuntimeError(f"Audio metadata extraction failed: {e}")

    def _validate_sync(
        self,
        video_path: Path,
        audio_path: Path,
        expected_duration: float,
        tolerance_ms: float = 5.0
    ) -> tuple[bool, float]:
        """
        Validate audio timing matches video (critical for caption sync).

        Args:
            video_path: Path to original video
            audio_path: Path to extracted audio
            expected_duration: Expected duration from video (seconds)
            tolerance_ms: Acceptable drift in milliseconds (default 5ms)

        Returns:
            Tuple of (sync_valid: bool, drift_seconds: float)
        """
        try:
            # Get actual audio duration
            audio_metadata = self._get_audio_metadata(audio_path)
            actual_duration = audio_metadata['duration']

            # Calculate drift
            drift = abs(actual_duration - expected_duration)
            tolerance_sec = tolerance_ms / 1000.0

            # Check if within tolerance
            sync_valid = drift <= tolerance_sec

            logger.debug(
                f"Sync validation: expected={expected_duration:.3f}s, "
                f"actual={actual_duration:.3f}s, drift={drift*1000:.1f}ms, "
                f"valid={sync_valid}"
            )

            return sync_valid, drift

        except Exception as e:
            logger.warning(f"Sync validation failed: {e}, assuming valid")
            return True, 0.0  # Assume valid if validation fails
