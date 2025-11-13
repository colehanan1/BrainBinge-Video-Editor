"""
Stage 7: Video Encoding

Hardware-accelerated video encoding using VideoToolbox (M2/M3 Mac) or
fallback to software encoding (libx264).

Encodes composed video to final deliverable format optimized for social
media platforms with H.265/HEVC compression.

Key Features:
    - VideoToolbox hardware acceleration (2-3× faster)
    - H.265/HEVC encoding (50% better compression vs H.264)
    - AAC audio encoding (192kbps, 48kHz stereo)
    - FastStart for web streaming
    - Automatic fallback to software encoding
    - File size validation (<30MB for 60s)

Example:
    >>> from src.modules.encoding import VideoEncoder
    >>> encoder = VideoEncoder(config)
    >>> result = encoder.process(
    ...     input_path="composed.mp4",
    ...     output_path="final.mp4"
    ... )
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import ffmpeg

from src.config import Config
from src.core.processor import BaseProcessor, ProcessorResult

logger = logging.getLogger(__name__)


class EncodingError(Exception):
    """Raised when video encoding fails."""
    pass


class VideoEncoder(BaseProcessor):
    """
    Hardware-accelerated video encoder with VideoToolbox support.

    Encodes composed video to final deliverable using M2/M3 GPU acceleration
    when available, with automatic fallback to software encoding.

    Encoding Settings:
        - Codec: H.265/HEVC (hevc_videotoolbox or libx265)
        - Video bitrate: 5000kbps (high quality for social)
        - Audio: AAC 192kbps, 48kHz stereo
        - FastStart: Enabled for web streaming
        - Color: yuv420p (universal compatibility)

    Args:
        config: Configuration object
        temp_dir: Directory for temporary files
    """

    # VideoToolbox settings (M2/M3 hardware encoding)
    VIDEOTOOLBOX_SETTINGS = {
        "vcodec": "hevc_videotoolbox",
        "b:v": "5000k",
        "profile:v": "main",
        "tag:v": "hvc1",  # QuickTime compatibility
        "acodec": "aac",
        "b:a": "192k",
        "ar": 48000,
        "ac": 2,
        "movflags": "+faststart",
        "pix_fmt": "yuv420p",
    }

    # Software fallback settings (libx264)
    LIBX264_SETTINGS = {
        "vcodec": "libx264",
        "preset": "medium",
        "crf": 23,
        "profile:v": "high",
        "level": "4.0",
        "acodec": "aac",
        "b:a": "192k",
        "ar": 48000,
        "ac": 2,
        "movflags": "+faststart",
        "pix_fmt": "yuv420p",
    }

    # Platform-specific size limits
    PLATFORM_LIMITS = {
        "instagram_reels": {"max_size_mb": 30, "max_duration": 90},
        "tiktok": {"max_size_mb": 287, "max_duration": 60},
        "youtube_shorts": {"max_size_mb": None, "max_duration": 60},
    }

    def __init__(self, config: Config, temp_dir: Optional[Path] = None):
        super().__init__(config, temp_dir)

        # Check VideoToolbox availability on init
        self.videotoolbox_available = self._check_videotoolbox_available()
        if self.videotoolbox_available:
            logger.info("VideoToolbox hardware acceleration available")
        else:
            logger.warning("VideoToolbox not available, will use software encoding")

    def process(
        self,
        input_path: Path,
        output_path: Path,
        **kwargs: Any,
    ) -> ProcessorResult:
        """
        Encode video with hardware acceleration.

        Args:
            input_path: Path to composed video from Stage 6
            output_path: Path for final encoded output
            **kwargs: Additional parameters
                - target_size_mb: Maximum file size in MB (default: 30)
                - bitrate: Video bitrate override (default: 5000k)
                - audio_bitrate: Audio bitrate override (default: 192k)

        Returns:
            ProcessorResult with encoding metadata

        Raises:
            EncodingError: If encoding fails completely
        """
        start_time = time.time()
        target_size_mb = kwargs.get("target_size_mb", 30)
        bitrate = kwargs.get("bitrate", "5000k")
        audio_bitrate = kwargs.get("audio_bitrate", "192k")

        logger.info(f"Starting video encoding: {input_path.name}")
        logger.info(f"Target size: {target_size_mb}MB")

        try:
            # Validate input
            errors = self.validate(input_path, **kwargs)
            if errors:
                raise EncodingError(f"Validation failed: {'; '.join(errors)}")

            # Attempt hardware encoding first
            if self.videotoolbox_available:
                try:
                    logger.info("Encoding with VideoToolbox (hardware acceleration)...")
                    self._encode_videotoolbox(input_path, output_path, bitrate, audio_bitrate)
                    encoder_used = "hevc_videotoolbox"
                except ffmpeg.Error as e:
                    logger.warning(f"VideoToolbox encoding failed: {e.stderr.decode() if e.stderr else str(e)}")
                    logger.info("Falling back to software encoding...")
                    self._encode_software(input_path, output_path, bitrate, audio_bitrate)
                    encoder_used = "libx264"
            else:
                logger.info("Encoding with libx264 (software)...")
                self._encode_software(input_path, output_path, bitrate, audio_bitrate)
                encoder_used = "libx264"

            # Validate output
            validation = self._validate_output(output_path, target_size_mb)

            processing_time = time.time() - start_time
            logger.info(f"Encoding completed in {processing_time:.1f}s")
            logger.info(f"Output: {validation['file_size_mb']:.1f}MB, {validation['duration_sec']:.1f}s")

            # Check size warning
            if validation["file_size_mb"] > target_size_mb:
                logger.warning(f"Output size ({validation['file_size_mb']:.1f}MB) exceeds target ({target_size_mb}MB)")

            return ProcessorResult(
                success=True,
                output_path=output_path,
                metadata={
                    "encoder": encoder_used,
                    "file_size_mb": validation["file_size_mb"],
                    "duration_sec": validation["duration_sec"],
                    "video_codec": validation["video_codec"],
                    "audio_codec": validation["audio_codec"],
                    "video_bitrate": validation["video_bitrate"],
                    "audio_bitrate": validation["audio_bitrate"],
                    "resolution": validation["resolution"],
                    "processing_time": round(processing_time, 2),
                    "hardware_accelerated": encoder_used == "hevc_videotoolbox",
                },
            )

        except EncodingError:
            raise
        except Exception as e:
            logger.error(f"Video encoding failed: {e}", exc_info=True)
            raise EncodingError(f"Video encoding failed: {e}")

    def _encode_videotoolbox(
        self,
        input_path: Path,
        output_path: Path,
        bitrate: str,
        audio_bitrate: str,
    ) -> None:
        """
        Encode with VideoToolbox hardware acceleration.

        Args:
            input_path: Input video path
            output_path: Output video path
            bitrate: Video bitrate (e.g., "5000k")
            audio_bitrate: Audio bitrate (e.g., "192k")

        Raises:
            ffmpeg.Error: If encoding fails
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        stream = ffmpeg.input(str(input_path))

        # Build settings with custom bitrates
        settings = self.VIDEOTOOLBOX_SETTINGS.copy()
        settings["b:v"] = bitrate
        settings["b:a"] = audio_bitrate

        # Pass settings directly - ffmpeg-python handles stream specifiers
        output = ffmpeg.output(stream, str(output_path), **settings)

        logger.debug(f"VideoToolbox command: {' '.join(ffmpeg.compile(output))}")

        ffmpeg.run(output, overwrite_output=True, capture_stderr=True)

    def _encode_software(
        self,
        input_path: Path,
        output_path: Path,
        bitrate: str,
        audio_bitrate: str,
    ) -> None:
        """
        Encode with software (libx264) fallback.

        Args:
            input_path: Input video path
            output_path: Output video path
            bitrate: Video bitrate (e.g., "5000k")
            audio_bitrate: Audio bitrate (e.g., "192k")

        Raises:
            ffmpeg.Error: If encoding fails
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        stream = ffmpeg.input(str(input_path))

        # Build settings
        settings = self.LIBX264_SETTINGS.copy()
        settings["b:a"] = audio_bitrate

        # Pass settings directly - ffmpeg-python handles stream specifiers
        output = ffmpeg.output(stream, str(output_path), **settings)

        logger.debug(f"libx264 command: {' '.join(ffmpeg.compile(output))}")

        ffmpeg.run(output, overwrite_output=True, capture_stderr=True)

    def _check_videotoolbox_available(self) -> bool:
        """
        Check if FFmpeg has VideoToolbox support.

        Returns:
            True if hevc_videotoolbox encoder is available
        """
        try:
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return "hevc_videotoolbox" in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _validate_output(self, output_path: Path, target_size_mb: int) -> Dict[str, Any]:
        """
        Validate encoded video meets requirements.

        Args:
            output_path: Path to encoded video
            target_size_mb: Target maximum file size

        Returns:
            Dict with file_size_mb, duration_sec, codec, bitrate, resolution
        """
        # Get file size
        file_size_bytes = output_path.stat().st_size
        file_size_mb = file_size_bytes / (1024 * 1024)

        # Probe video with ffprobe
        try:
            probe = ffmpeg.probe(str(output_path))

            # Extract video stream info
            video_stream = next(
                (s for s in probe["streams"] if s["codec_type"] == "video"), None
            )
            audio_stream = next(
                (s for s in probe["streams"] if s["codec_type"] == "audio"), None
            )

            duration = float(probe["format"].get("duration", 0))
            video_codec = video_stream["codec_name"] if video_stream else "unknown"
            audio_codec = audio_stream["codec_name"] if audio_stream else "unknown"

            # Video bitrate
            video_bitrate = video_stream.get("bit_rate", "unknown") if video_stream else "unknown"
            if video_bitrate != "unknown":
                video_bitrate = f"{int(video_bitrate) // 1000}k"

            # Audio bitrate
            audio_bitrate = audio_stream.get("bit_rate", "unknown") if audio_stream else "unknown"
            if audio_bitrate != "unknown":
                audio_bitrate = f"{int(audio_bitrate) // 1000}k"

            # Resolution
            if video_stream:
                width = video_stream.get("width", 0)
                height = video_stream.get("height", 0)
                resolution = f"{width}×{height}"
            else:
                resolution = "unknown"

            return {
                "file_size_mb": round(file_size_mb, 2),
                "duration_sec": round(duration, 1),
                "video_codec": video_codec,
                "audio_codec": audio_codec,
                "video_bitrate": video_bitrate,
                "audio_bitrate": audio_bitrate,
                "resolution": resolution,
            }

        except ffmpeg.Error as e:
            logger.warning(f"Failed to probe output video: {e}")
            return {
                "file_size_mb": round(file_size_mb, 2),
                "duration_sec": 0,
                "video_codec": "unknown",
                "audio_codec": "unknown",
                "video_bitrate": "unknown",
                "audio_bitrate": "unknown",
                "resolution": "unknown",
            }

    def validate(self, input_path: Path, **kwargs: Any) -> List[str]:
        """
        Validate input before encoding.

        Args:
            input_path: Path to input video
            **kwargs: Additional parameters

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check input exists
        if not input_path.exists():
            errors.append(f"Input video not found: {input_path}")
        elif input_path.stat().st_size == 0:
            errors.append("Input video file is empty")

        return errors

    def estimate_duration(self, input_path: Path, **kwargs: Any) -> float:
        """
        Estimate encoding duration.

        Args:
            input_path: Path to input video

        Returns:
            Estimated time in seconds
        """
        try:
            # Probe video duration
            probe = ffmpeg.probe(str(input_path))
            duration = float(probe["format"].get("duration", 0))

            # VideoToolbox: ~0.3× realtime (60s video in ~20s)
            # Software: ~1.0× realtime (60s video in ~60s)
            if self.videotoolbox_available:
                return duration * 0.3
            else:
                return duration * 1.0

        except Exception:
            # Fallback estimate
            return 30.0
