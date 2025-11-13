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

    def process(
        self,
        input_path: Path,
        output_path: Path,
        **kwargs: Any,
    ) -> ProcessorResult:
        """
        Extract audio from video.

        Args:
            input_path: Path to input video (MP4)
            output_path: Path for output audio (WAV)
            **kwargs: Additional parameters

        Returns:
            ProcessorResult with extracted audio path

        Raises:
            ProcessingError: If audio extraction fails
        """
        logger.info(f"Extracting audio from {input_path} to {output_path}")

        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Extract audio using ffmpeg-python
            stream = ffmpeg.input(str(input_path))
            stream = ffmpeg.output(
                stream,
                str(output_path),
                format='wav',
                acodec='pcm_s16le',  # 16-bit PCM
                ac=self.channels,     # Mono
                ar=self.sample_rate,  # 16kHz
            )

            # Run ffmpeg
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)

            # Validate output
            if not output_path.exists():
                raise RuntimeError(f"Audio extraction failed: {output_path} not created")

            if output_path.stat().st_size == 0:
                raise RuntimeError(f"Audio extraction failed: {output_path} is empty")

            logger.info(f"Audio extracted successfully: {output_path.stat().st_size} bytes")

            return ProcessorResult(
                success=True,
                output_path=output_path,
                metadata={
                    'sample_rate': self.sample_rate,
                    'channels': self.channels,
                    'format': 'wav',
                    'size_bytes': output_path.stat().st_size,
                }
            )

        except ffmpeg.Error as e:
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

        except ffmpeg.Error as e:
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
            estimated_time = video_duration * 0.1

            logger.debug(f"Estimated audio extraction time: {estimated_time:.2f}s for {video_duration:.2f}s video")

            return estimated_time

        except Exception as e:
            logger.warning(f"Could not estimate duration: {e}, using default")
            return 5.0  # Default fallback
