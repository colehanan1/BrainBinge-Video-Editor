"""
Stage 6: Video Composition

Combines all video elements using FFmpeg complex filter graphs.

Composes final video with:
- Main video (HeyGen) scaled to 1280×720
- Header overlay (drawtext filter)
- Burned ASS captions (subtitles filter)
- B-roll overlays (PIP or fullframe)
- Audio ducking during B-roll
- Fade transitions

All processing in single FFmpeg pass (no intermediate files).

Key Features:
    - Complex filter graph construction
    - Picture-in-Picture (PIP) B-roll
    - Fullframe B-roll replacement
    - Audio volume ducking
    - Header text overlay
    - ASS caption burning

Example:
    >>> from src.modules.composer import VideoComposer
    >>> composer = VideoComposer(config)
    >>> result = composer.process(
    ...     main_video="video.mp4",
    ...     captions_ass="styled.ass",
    ...     output_path="composed.mp4"
    ... )
"""

import logging
import platform
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import ffmpeg

from src.config import Config
from src.core.processor import BaseProcessor, ProcessorResult

logger = logging.getLogger(__name__)


class CompositionError(Exception):
    """Raised when video composition fails."""
    pass


class VideoComposer(BaseProcessor):
    """
    Compose final video with all overlays using FFmpeg filter graphs.

    Combines main video, captions, header, and B-roll into single output
    using a complex FFmpeg filter graph. All processing happens in one pass
    for optimal speed and quality.

    Filter Graph Structure:
        1. Scale main video to 1280×720
        2. Add header overlay (drawtext)
        3. Burn ASS captions (subtitles)
        4. Add B-roll overlays (PIP or fullframe)
        5. Apply fade transitions
        6. Audio ducking during B-roll

    Args:
        config: Configuration object
        temp_dir: Directory for temporary files
    """

    def __init__(self, config: Config, temp_dir: Optional[Path] = None):
        super().__init__(config, temp_dir)

        # Get brand configuration for header
        brand_config = getattr(config, "brand", {})

        # Handle various brand config formats
        if hasattr(brand_config, "name"):
            # Pydantic model with name attribute
            self.brand_name = brand_config.name
        elif isinstance(brand_config, dict) and "name" in brand_config:
            # Dict with name key
            self.brand_name = brand_config["name"]
        elif isinstance(brand_config, str):
            # Brand name as string
            self.brand_name = brand_config
        else:
            # Default fallback
            self.brand_name = "BrainBinge"

        # Video dimensions (standard for social media)
        self.video_width = 1280
        self.video_height = 720

        # B-roll settings
        broll_config = getattr(config, "broll", {})

        # Handle dict vs Pydantic model
        if isinstance(broll_config, dict):
            self.pip_enabled = broll_config.get("pip_enabled", False)  # Default to fullframe
        else:
            self.pip_enabled = getattr(broll_config, "pip_enabled", False)
        self.pip_width = 400  # PIP width (400px = ~31% of 1280)
        self.pip_height = 300  # PIP height (300px = ~42% of 720)
        self.pip_padding = 10  # Padding from edges
        self.max_broll_duration = 3.5  # Maximum B-roll duration in seconds

        # Transition settings
        self.fade_duration = 0.3  # 300ms fade in/out (faster for TikTok-style)

        # Audio ducking
        self.ducking_volume = 0.5  # 50% volume during B-roll

    def process(
        self,
        input_path: Path,
        output_path: Path,
        captions_path: Optional[Path] = None,
        broll_clips: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ProcessorResult:
        """
        Compose final video with all overlays.

        Args:
            input_path: Path to main video (HeyGen)
            output_path: Path for composed output
            captions_path: Path to ASS caption file (optional)
            broll_clips: List of B-roll clip dicts (optional)
                Each dict: {
                    "path": Path,
                    "start_time": float,
                    "end_time": float,
                    "type": "pip" | "fullframe"
                }
            **kwargs: Additional parameters
                - header_text: Override header text
                - video_width: Override video width (default: 1280)
                - video_height: Override video height (default: 720)

        Returns:
            ProcessorResult with composed video and metadata

        Raises:
            CompositionError: If composition fails
        """
        start_time = time.time()
        header_text = kwargs.get("header_text", f"{self.brand_name} Video")
        video_width = kwargs.get("video_width", self.video_width)
        video_height = kwargs.get("video_height", self.video_height)
        broll_clips = broll_clips or []

        logger.info(f"Starting video composition: {input_path.name}")
        logger.info(f"Output resolution: {video_width}×{video_height}")
        logger.info(f"B-roll clips: {len(broll_clips)}")

        try:
            # Validate inputs
            errors = self.validate(input_path, captions_path=captions_path, **kwargs)
            if errors:
                raise CompositionError(f"Validation failed: {'; '.join(errors)}")

            # Build and execute filter graph
            logger.info("Building FFmpeg filter graph...")
            self._compose_video(
                main_video=input_path,
                output_path=output_path,
                captions_path=captions_path,
                header_text=header_text,
                broll_clips=broll_clips,
                video_width=video_width,
                video_height=video_height,
            )

            processing_time = time.time() - start_time
            logger.info(f"Composition completed in {processing_time:.1f}s")
            logger.info(f"Output saved to: {output_path}")

            return ProcessorResult(
                success=True,
                output_path=output_path,
                metadata={
                    "video_resolution": f"{video_width}×{video_height}",
                    "header_text": header_text,
                    "captions_enabled": captions_path is not None,
                    "broll_count": len(broll_clips),
                    "processing_time": round(processing_time, 2),
                },
            )

        except CompositionError:
            raise
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
            raise CompositionError(f"FFmpeg composition failed: {e}")
        except Exception as e:
            logger.error(f"Video composition failed: {e}")
            raise CompositionError(f"Video composition failed: {e}")

    def _compose_video(
        self,
        main_video: Path,
        output_path: Path,
        captions_path: Optional[Path],
        header_text: str,
        broll_clips: List[Dict[str, Any]],
        video_width: int,
        video_height: int,
    ) -> None:
        """
        Execute FFmpeg composition with complex filter graph.

        Args:
            main_video: Path to main video
            output_path: Path for output
            captions_path: Path to ASS captions (optional)
            header_text: Header text to display
            broll_clips: List of B-roll clip dicts
            video_width: Output video width
            video_height: Output video height
        """
        # Load main video
        main = ffmpeg.input(str(main_video))

        # Build video filter chain
        video = self._build_video_filters(
            main_stream=main.video,
            captions_path=captions_path,
            header_text=header_text,
            broll_clips=broll_clips,
            video_width=video_width,
            video_height=video_height,
        )

        # Build audio filter chain
        audio = self._build_audio_filters(
            main_stream=main.audio,
            broll_clips=broll_clips,
        )

        # Create output with intermediate quality
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output = ffmpeg.output(
            video,
            audio,
            str(output_path),
            vcodec='libx264',
            preset='ultrafast',  # Speed over compression (will re-encode in Stage 7)
            crf=18,  # High quality intermediate
            acodec='aac',
            audio_bitrate='192k',
        )

        # Run FFmpeg
        logger.info("Executing FFmpeg composition...")
        ffmpeg.run(output, overwrite_output=True, capture_stderr=True)

    def _build_video_filters(
        self,
        main_stream: ffmpeg.Stream,
        captions_path: Optional[Path],
        header_text: str,
        broll_clips: List[Dict[str, Any]],
        video_width: int,
        video_height: int,
    ) -> ffmpeg.Stream:
        """
        Build video filter chain.

        Args:
            main_stream: Main video stream from ffmpeg.input()
            captions_path: Path to ASS captions
            header_text: Header text
            broll_clips: B-roll clips to overlay
            video_width: Output width
            video_height: Output height

        Returns:
            Final video stream with all filters applied
        """
        # Step 1: Scale to target resolution
        video = main_stream.filter('scale', video_width, video_height)

        # Step 2: Add header overlay
        video = self._add_header_overlay(video, header_text, video_width)

        # Step 3: Add B-roll overlays (BEFORE captions so captions appear on top)
        for clip in broll_clips:
            clip_type = clip.get("type", "pip")
            if clip_type == "pip":
                video = self._add_broll_pip(video, clip)
            elif clip_type == "fullframe":
                video = self._add_broll_fullframe(video, clip, video_width, video_height)

        # Step 4: Burn captions (AFTER B-roll so they appear on all footage)
        if captions_path and captions_path.exists():
            video = self._burn_captions(video, captions_path)

        return video

    def _build_audio_filters(
        self,
        main_stream: ffmpeg.Stream,
        broll_clips: List[Dict[str, Any]],
    ) -> ffmpeg.Stream:
        """
        Build audio filter chain with ducking.

        Args:
            main_stream: Main audio stream
            broll_clips: B-roll clips (for ducking intervals)

        Returns:
            Audio stream with ducking applied
        """
        if not broll_clips:
            return main_stream

        # Extract B-roll intervals for ducking
        intervals = [(clip["start_time"], clip["end_time"]) for clip in broll_clips]

        # Apply audio ducking
        return self._apply_audio_ducking(main_stream, intervals)

    def _add_header_overlay(
        self,
        stream: ffmpeg.Stream,
        header_text: str,
        video_width: int,
    ) -> ffmpeg.Stream:
        """
        Add header overlay using drawtext filter.

        Args:
            stream: Input video stream
            header_text: Text to display
            video_width: Video width for centering

        Returns:
            Stream with header overlay
        """
        logger.debug(f"Adding header overlay: '{header_text}'")

        # Use drawtext filter for header with TikTok-style aesthetics
        # Lilac text with blue transparent box - only show for first 7 seconds
        return stream.drawtext(
            text=header_text,
            fontfile='/System/Library/Fonts/Supplemental/Impact.ttf',  # Cool font (fallback to system default if not found)
            fontsize=52,  # Larger for prominence
            fontcolor='#C8A2C8',  # Lilac/purple color
            x='(w-text_w)/2',  # Centered horizontally
            y='40',  # 40px from top
            box=1,  # Enable background box
            boxcolor='#0066FF@0.25',  # Blue with 25% transparency (75% opaque)
            boxborderw=15,  # Wider padding for better spacing
            enable='lt(t,7)',  # Only show for first 7 seconds (t < 7)
        )

    def _burn_captions(
        self,
        stream: ffmpeg.Stream,
        captions_path: Path,
    ) -> ffmpeg.Stream:
        """
        Burn ASS captions using subtitles filter.

        Args:
            stream: Input video stream
            captions_path: Path to ASS caption file

        Returns:
            Stream with burned captions
        """
        logger.debug(f"Burning captions from {captions_path}")

        # Escape path for FFmpeg subtitles filter
        # Windows paths need special escaping
        path_str = str(captions_path)

        if platform.system() == "Windows":
            # Escape backslashes and colons for Windows
            path_str = path_str.replace('\\', '\\\\').replace(':', '\\:')
        else:
            # Unix paths just need colon escaping
            path_str = path_str.replace(':', '\\:')

        return stream.filter('subtitles', filename=path_str)

    def _add_broll_pip(
        self,
        main_stream: ffmpeg.Stream,
        clip_data: Dict[str, Any],
    ) -> ffmpeg.Stream:
        """
        Add picture-in-picture B-roll with fade transitions.

        Args:
            main_stream: Main video stream
            clip_data: Dict with path, start_time, end_time

        Returns:
            Stream with PIP B-roll overlaid
        """
        clip_path = Path(clip_data["path"])  # Convert string to Path
        start = clip_data["start_time"]
        end = clip_data["end_time"]

        logger.debug(f"Adding PIP B-roll: {clip_path.name} ({start}s-{end}s)")

        # Load and process B-roll clip
        broll = (
            ffmpeg.input(str(clip_path))
            .filter('scale', self.pip_width, self.pip_height)
            .filter('fade', type='in', start_time=start, duration=self.fade_duration)
            .filter('fade', type='out', start_time=end - self.fade_duration, duration=self.fade_duration)
        )

        # Overlay at bottom-right corner
        return main_stream.overlay(
            broll,
            x=f'main_w-{self.pip_width + self.pip_padding}',  # 10px from right edge
            y=f'main_h-{self.pip_height + self.pip_padding}',  # 10px from bottom
            enable=f'between(t,{start},{end})',  # Show only during interval
        )

    def _add_broll_fullframe(
        self,
        main_stream: ffmpeg.Stream,
        clip_data: Dict[str, Any],
        video_width: int,
        video_height: int,
    ) -> ffmpeg.Stream:
        """
        Replace main video with fullframe B-roll during interval.

        Args:
            main_stream: Main video stream
            clip_data: Dict with path, start_time, end_time
            video_width: Output video width
            video_height: Output video height

        Returns:
            Stream with fullframe B-roll overlaid
        """
        clip_path = Path(clip_data["path"])  # Convert string to Path
        start = clip_data["start_time"]
        end = clip_data["end_time"]
        duration = end - start

        # Enforce maximum B-roll duration
        if duration > self.max_broll_duration:
            logger.debug(f"Trimming B-roll from {duration:.1f}s to {self.max_broll_duration}s")
            duration = self.max_broll_duration
            end = start + duration

        logger.debug(f"Adding fullframe B-roll: {clip_path.name} ({start}s-{end}s, {duration:.1f}s)")

        # Load, trim, and process B-roll clip
        broll = (
            ffmpeg.input(str(clip_path), ss=0, t=duration)
            .filter('scale', video_width, video_height)
            .filter('fade', type='in', duration=self.fade_duration)
            .filter('fade', type='out', start_time=duration - self.fade_duration, duration=self.fade_duration)
            .filter('setpts', f'PTS+{start}/TB')  # Shift timeline to start time
        )

        # Overlay at full opacity (replaces main video during interval)
        return main_stream.overlay(
            broll,
            enable=f'between(t,{start},{end})',
        )

    def _apply_audio_ducking(
        self,
        audio_stream: ffmpeg.Stream,
        broll_intervals: List[Tuple[float, float]],
    ) -> ffmpeg.Stream:
        """
        Reduce audio volume during B-roll intervals.

        Args:
            audio_stream: Main audio stream
            broll_intervals: List of (start, end) tuples in seconds

        Returns:
            Audio stream with ducking applied
        """
        if not broll_intervals:
            return audio_stream

        logger.debug(f"Applying audio ducking: {len(broll_intervals)} intervals")

        # Build volume expression with conditional ducking
        # Example: "if(between(t,5,12),0.5,1.0)*if(between(t,15,25),0.5,1.0)"
        conditions = '*'.join([
            f"if(between(t,{start},{end}),{self.ducking_volume},1.0)"
            for start, end in broll_intervals
        ])

        return audio_stream.filter('volume', conditions)

    def validate(
        self,
        input_path: Path,
        captions_path: Optional[Path] = None,
        **kwargs: Any,
    ) -> List[str]:
        """
        Validate inputs before composition.

        Args:
            input_path: Path to main video
            captions_path: Path to captions (optional)
            **kwargs: Additional parameters

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check main video
        if not input_path.exists():
            errors.append(f"Main video not found: {input_path}")
        elif input_path.stat().st_size == 0:
            errors.append("Main video file is empty")

        # Check captions (if provided)
        if captions_path:
            if not captions_path.exists():
                errors.append(f"Captions file not found: {captions_path}")
            elif captions_path.stat().st_size == 0:
                errors.append("Captions file is empty")
            elif not captions_path.suffix.lower() == '.ass':
                errors.append(f"Captions must be ASS format, got: {captions_path.suffix}")

        # Check B-roll clips (if provided)
        broll_clips = kwargs.get("broll_clips", [])
        for i, clip in enumerate(broll_clips):
            if "path" not in clip:
                errors.append(f"B-roll clip {i} missing 'path' field")
                continue

            clip_path = clip["path"]
            if not Path(clip_path).exists():
                errors.append(f"B-roll clip not found: {clip_path}")

            if "start_time" not in clip or "end_time" not in clip:
                errors.append(f"B-roll clip {i} missing timing fields")

        return errors

    def estimate_duration(self, input_path: Path, **kwargs: Any) -> float:
        """
        Estimate composition duration.

        Composition time depends on video length and number of overlays.
        Roughly 0.5-1x realtime with ultrafast preset.

        Args:
            input_path: Path to main video
            **kwargs: Additional parameters

        Returns:
            Estimated time in seconds
        """
        try:
            # Get video duration
            probe = ffmpeg.probe(str(input_path))
            duration = float(probe["format"]["duration"])

            # Composition typically takes 0.5-1x video duration with ultrafast
            # More B-roll clips = slightly longer processing
            broll_clips = kwargs.get("broll_clips", [])
            multiplier = 0.5 + (len(broll_clips) * 0.05)  # +5% per B-roll clip

            return duration * multiplier
        except Exception:
            # Fallback estimate
            return 60.0
