"""
Transition Engine for Video Composition

Implements professional xfade transitions between avatar and B-roll segments
using FFmpeg's xfade filter with 44+ transition effects.

Key Features:
    - Segment-based video composition
    - Dynamic xfade filter chain generation
    - Configurable transition types per segment
    - Audio crossfading support
    - Smooth/dramatic transition styles

Example:
    >>> from src.modules.transitions import TransitionEngine
    >>> engine = TransitionEngine(config)
    >>> result = engine.compose_with_transitions(
    ...     main_video="avatar.mp4",
    ...     broll_clips=broll_data,
    ...     output="final.mp4"
    ... )
"""

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import ffmpeg

from src.config import Config
from src.core.processor import BaseProcessor, ProcessorResult

logger = logging.getLogger(__name__)


class TransitionError(Exception):
    """Raised when transition generation fails."""
    pass


class TransitionEngine(BaseProcessor):
    """
    Generate professional video transitions using FFmpeg xfade filter.

    Composes video by:
    1. Splitting into segments (avatar/B-roll alternating)
    2. Applying xfade transitions between segments
    3. Supporting multiple transition types (fade, slide, circle, zoom, etc.)
    4. Audio crossfading for smooth sound transitions

    Args:
        config: Configuration object
        temp_dir: Directory for temporary files
    """

    # Transition types mapped to styles
    SMOOTH_TRANSITIONS = ['fade', 'dissolve', 'fadeblack', 'fadewhite']
    DRAMATIC_TRANSITIONS = ['circleopen', 'circleclose', 'zoomin', 'radial']
    SLIDE_TRANSITIONS = ['slideright', 'slideleft', 'slideup', 'slidedown']
    WIPE_TRANSITIONS = ['wipeleft', 'wiperight', 'wipeup', 'wipedown']

    def __init__(self, config: Config, temp_dir: Optional[Path] = None):
        super().__init__(config, temp_dir)

        # Transition settings
        self.default_transition = 'fade'
        self.default_duration = 0.5  # 500ms
        self.audio_crossfade = True

        # Pattern for varied transitions
        self.transition_pattern = [
            'slideright',   # Avatar → B-roll: Dynamic slide
            'fade',         # B-roll → Avatar: Smooth fade
            'dissolve',     # Avatar → B-roll: Smooth dissolve
            'circleopen',   # B-roll → Avatar: Dramatic circle
            'slideright',   # Avatar → B-roll: Dynamic slide
            'zoomin',       # B-roll → Avatar: Dramatic zoom
        ]

    def generate_segments(
        self,
        main_video_path: Path,
        main_duration: float,
        broll_clips: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Generate video segments from B-roll plan.

        Creates alternating segments of avatar and B-roll footage with
        transition points and types.

        Args:
            main_video_path: Path to main avatar video
            main_duration: Total duration of avatar video
            broll_clips: List of B-roll clip dicts with start/end times

        Returns:
            List of segment dicts with:
                - type: 'avatar' or 'broll'
                - source: Path to video file
                - start: Start time in source video
                - end: End time in source video
                - duration: Segment duration
                - transition_in: Transition type when entering this segment
                - transition_duration: Duration of transition
        """
        segments = []
        current_time = 0.0
        transition_idx = 0

        # Sort B-roll clips by start time
        sorted_broll = sorted(broll_clips, key=lambda x: x['start_time'])

        for i, broll in enumerate(sorted_broll):
            broll_start = broll['start_time']
            broll_end = broll['end_time']
            broll_duration = broll_end - broll_start

            # Add avatar segment before this B-roll (if there's time)
            if current_time < broll_start:
                avatar_duration = broll_start - current_time
                transition_type = self._get_transition_type(transition_idx)

                segments.append({
                    'type': 'avatar',
                    'source': main_video_path,
                    'start': current_time,
                    'end': broll_start,
                    'duration': avatar_duration,
                    'transition_in': transition_type if i > 0 else None,  # No transition for first segment
                    'transition_duration': self.default_duration,
                    'segment_index': len(segments),
                })

                transition_idx += 1

            # Add B-roll segment
            transition_type = self._get_transition_type(transition_idx)

            segments.append({
                'type': 'broll',
                'source': Path(broll['path']),
                'start': 0,  # B-roll starts from beginning
                'end': broll_duration,
                'duration': broll_duration,
                'transition_in': transition_type,
                'transition_duration': self.default_duration,
                'segment_index': len(segments),
            })

            transition_idx += 1
            current_time = broll_end

        # Add final avatar segment if video continues
        if current_time < main_duration:
            transition_type = self._get_transition_type(transition_idx)

            segments.append({
                'type': 'avatar',
                'source': main_video_path,
                'start': current_time,
                'end': main_duration,
                'duration': main_duration - current_time,
                'transition_in': transition_type,
                'transition_duration': self.default_duration,
                'segment_index': len(segments),
            })

        logger.info(f"Generated {len(segments)} segments for transitions")
        return segments

    def _get_transition_type(self, index: int) -> str:
        """
        Get transition type based on pattern cycling.

        Args:
            index: Transition index

        Returns:
            Transition type name
        """
        return self.transition_pattern[index % len(self.transition_pattern)]

    def build_xfade_filter_chain(
        self,
        segments: List[Dict[str, Any]],
        video_width: int = 1280,
        video_height: int = 720,
    ) -> str:
        """
        Build FFmpeg filter_complex for xfade transitions.

        Creates a complex filter graph that:
        1. Loads all segment videos as inputs
        2. Chains xfade transitions between them
        3. Outputs final composited video

        Args:
            segments: List of segment dicts
            video_width: Output width
            video_height: Output height

        Returns:
            filter_complex string for FFmpeg
        """
        filter_parts = []

        # Input preparation - scale all segments
        for i, seg in enumerate(segments):
            filter_parts.append(
                f"[{i}:v]scale={video_width}:{video_height},"
                f"setsar=1[v{i}]"
            )

        # Build xfade chain
        current_label = "v0"

        for i in range(1, len(segments)):
            seg = segments[i]
            transition = seg['transition_in']
            duration = seg['transition_duration']

            # Calculate offset (cumulative duration up to this point minus transition)
            offset = sum(s['duration'] for s in segments[:i]) - duration

            next_label = f"v{i}" if i < len(segments) - 1 else "vout"

            if transition:
                filter_parts.append(
                    f"[{current_label}][v{i}]xfade="
                    f"transition={transition}:"
                    f"duration={duration}:"
                    f"offset={offset:.2f}"
                    f"[{next_label}]"
                )
                current_label = next_label

        return ";".join(filter_parts)

    def build_audio_crossfade_chain(
        self,
        segments: List[Dict[str, Any]],
    ) -> str:
        """
        Build audio crossfade filter chain.

        Args:
            segments: List of segment dicts

        Returns:
            Audio filter_complex string
        """
        if not self.audio_crossfade:
            return "[0:a]acopy[aout]"

        filter_parts = []
        current_label = "0:a"

        for i in range(1, len(segments)):
            seg = segments[i]
            duration = seg['transition_duration']

            # Audio crossfade between segments
            next_label = f"a{i}" if i < len(segments) - 1 else "aout"

            filter_parts.append(
                f"[{current_label}][{i}:a]acrossfade="
                f"d={duration}:"
                f"c1=tri:"
                f"c2=tri"
                f"[{next_label}]"
            )
            current_label = next_label

        return ";".join(filter_parts) if filter_parts else f"[{current_label}]acopy[aout]"

    def compose_segments_with_transitions(
        self,
        segments: List[Dict[str, Any]],
        output_path: Path,
        video_width: int = 1280,
        video_height: int = 720,
    ) -> None:
        """
        Compose all segments with xfade transitions.

        Args:
            segments: List of segment dicts
            output_path: Output video path
            video_width: Output width
            video_height: Output height

        Raises:
            TransitionError: If composition fails
        """
        try:
            # Build filter chains
            video_filter = self.build_xfade_filter_chain(segments, video_width, video_height)
            audio_filter = self.build_audio_crossfade_chain(segments)

            # Combine filters
            filter_complex = f"{video_filter};{audio_filter}"

            logger.debug(f"Filter complex: {filter_complex}")

            # Create output
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Build input list for FFmpeg
            input_args = []
            for seg in segments:
                source = seg['source']
                start = seg['start']
                duration = seg['duration']

                # Add input arguments
                input_args.extend(['-ss', str(start), '-t', str(duration), '-i', str(source)])

            # Build FFmpeg command
            cmd = ['ffmpeg', '-y']  # -y to overwrite output
            cmd.extend(input_args)
            cmd.extend([
                '-filter_complex', filter_complex,
                '-map', '[vout]',
                '-map', '[aout]',
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-crf', '18',
                '-c:a', 'aac',
                '-b:a', '192k',
                str(output_path)
            ])

            logger.info("Executing FFmpeg with xfade transitions...")
            logger.debug(f"FFmpeg command: {' '.join(cmd)}")

            # Run FFmpeg command
            import subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise TransitionError(f"FFmpeg failed: {result.stderr}")

            logger.info("Transition composition completed successfully")

        except TransitionError:
            raise
        except Exception as e:
            logger.error(f"Transition composition failed: {e}")
            raise TransitionError(f"Transition composition failed: {e}")

    def get_video_duration(self, video_path: Path) -> float:
        """
        Get video duration using ffprobe.

        Args:
            video_path: Path to video file

        Returns:
            Duration in seconds
        """
        try:
            probe = ffmpeg.probe(str(video_path))
            duration = float(probe['format']['duration'])
            return duration
        except Exception as e:
            logger.warning(f"Failed to probe video duration: {e}")
            return 60.0  # Fallback

    def process(
        self,
        input_path: Path,
        output_path: Path,
        broll_clips: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ProcessorResult:
        """
        Process video with transitions.

        Args:
            input_path: Main avatar video
            output_path: Output path
            broll_clips: List of B-roll clips with timings
            **kwargs: Additional parameters

        Returns:
            ProcessorResult with transition metadata
        """
        start_time = time.time()
        broll_clips = broll_clips or []

        logger.info(f"Starting transition composition: {input_path.name}")
        logger.info(f"B-roll clips: {len(broll_clips)}")

        try:
            # Get main video duration
            main_duration = self.get_video_duration(input_path)

            # Generate segments
            segments = self.generate_segments(input_path, main_duration, broll_clips)

            # Log segment plan
            for seg in segments:
                logger.info(
                    f"  Segment {seg['segment_index']}: {seg['type']} "
                    f"({seg['duration']:.1f}s) transition={seg.get('transition_in', 'none')}"
                )

            # Compose with transitions
            self.compose_segments_with_transitions(
                segments,
                output_path,
                video_width=kwargs.get('video_width', 1280),
                video_height=kwargs.get('video_height', 720),
            )

            processing_time = time.time() - start_time
            logger.info(f"Transition composition completed in {processing_time:.1f}s")

            return ProcessorResult(
                success=True,
                output_path=output_path,
                metadata={
                    'segment_count': len(segments),
                    'transition_count': len(segments) - 1,
                    'processing_time': round(processing_time, 2),
                }
            )

        except TransitionError:
            raise
        except Exception as e:
            logger.error(f"Transition processing failed: {e}")
            raise TransitionError(f"Transition processing failed: {e}")
