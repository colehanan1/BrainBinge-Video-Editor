"""
CLI Helper Utilities

Provides utilities for CLI orchestration including stage timing,
error recovery, and progress reporting.

Example:
    >>> from src.utils.cli_helpers import stage_timer, safe_stage_execution
    >>> with stage_timer("Stage 1: Audio Extraction"):
    ...     result = extract_audio(video)
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@contextmanager
def stage_timer(stage_name: str, logger_instance: Optional[logging.Logger] = None):
    """
    Time stage execution with automatic logging.

    Args:
        stage_name: Name of the stage being timed
        logger_instance: Optional logger instance (defaults to module logger)

    Yields:
        Dictionary to store stage metadata

    Example:
        >>> with stage_timer("Stage 1: Audio Extraction") as timer:
        ...     result = extract_audio(video)
        ...     timer['file_size'] = result.size
    """
    log = logger_instance or logger
    start = time.time()
    metadata = {}

    log.info(f"Starting: {stage_name}")

    try:
        yield metadata
    finally:
        duration = time.time() - start
        log.info(f"Completed: {stage_name} ({duration:.1f}s)")
        metadata['duration'] = duration


def safe_stage_execution(
    stage_func: Callable,
    *args,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    retry_on: tuple = (Exception,),
    logger_instance: Optional[logging.Logger] = None,
    **kwargs
) -> Any:
    """
    Execute stage with error handling and exponential backoff retry logic.

    Args:
        stage_func: Function to execute
        *args: Positional arguments for stage_func
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier (2.0 = 2s, 4s, 8s...)
        retry_on: Tuple of exception types to retry on
        logger_instance: Optional logger instance
        **kwargs: Keyword arguments for stage_func

    Returns:
        Result from successful stage execution

    Raises:
        Exception: If all retry attempts fail

    Example:
        >>> result = safe_stage_execution(
        ...     fetch_broll,
        ...     plan_path,
        ...     max_retries=3,
        ...     retry_on=(RequestException, TimeoutError)
        ... )
    """
    log = logger_instance or logger

    for attempt in range(max_retries):
        try:
            return stage_func(*args, **kwargs)
        except retry_on as e:
            if attempt == max_retries - 1:
                # Last attempt failed - re-raise
                log.error(f"Stage failed after {max_retries} attempts: {e}")
                raise

            # Calculate backoff time
            wait_time = backoff_factor ** attempt
            log.warning(
                f"Attempt {attempt + 1}/{max_retries} failed: {e}"
            )
            log.info(f"Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)


def validate_inputs(
    video_path: Optional[Path] = None,
    script_path: Optional[Path] = None,
    broll_plan_path: Optional[Path] = None,
    config_path: Optional[Path] = None,
    require_pexels_key: bool = False,
) -> list[str]:
    """
    Validate all inputs before starting pipeline.

    Args:
        video_path: Path to input video
        script_path: Path to script file
        broll_plan_path: Path to B-roll plan CSV
        config_path: Path to configuration file
        require_pexels_key: Whether to require PEXELS_API_KEY

    Returns:
        List of validation error messages (empty if valid)

    Example:
        >>> errors = validate_inputs(
        ...     video_path=Path("video.mp4"),
        ...     script_path=Path("script.txt")
        ... )
        >>> if errors:
        ...     print("\\n".join(errors))
    """
    import os

    errors = []

    # Check video format
    if video_path:
        if not video_path.exists():
            errors.append(f"Video file not found: {video_path}")
        elif video_path.suffix.lower() not in ['.mp4', '.mov', '.avi']:
            errors.append(
                f"Unsupported video format: {video_path.suffix}. "
                "Supported formats: .mp4, .mov, .avi"
            )

    # Check script not empty
    if script_path:
        if not script_path.exists():
            errors.append(f"Script file not found: {script_path}")
        elif script_path.stat().st_size == 0:
            errors.append("Script file is empty")

    # Check B-roll plan format
    if broll_plan_path:
        if not broll_plan_path.exists():
            errors.append(f"B-roll plan not found: {broll_plan_path}")
        elif broll_plan_path.suffix.lower() != '.csv':
            errors.append(
                f"B-roll plan must be CSV format, got: {broll_plan_path.suffix}"
            )

    # Check config exists
    if config_path:
        if not config_path.exists():
            errors.append(f"Config file not found: {config_path}")
        elif config_path.suffix.lower() not in ['.yaml', '.yml', '.json']:
            errors.append(
                f"Unsupported config format: {config_path.suffix}. "
                "Supported formats: .yaml, .yml, .json"
            )

    # Check Pexels API key
    if require_pexels_key and not os.getenv('PEXELS_API_KEY'):
        errors.append(
            "PEXELS_API_KEY not found in environment. "
            "Set it in .env file or environment variables."
        )

    return errors


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted string (e.g., "24.3 MB")

    Example:
        >>> format_file_size(25542656)
        '24.4 MB'
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def print_stage_header(stage_num: int, total_stages: int, stage_name: str):
    """
    Print formatted stage header.

    Args:
        stage_num: Current stage number (1-indexed)
        total_stages: Total number of stages
        stage_name: Name of the stage

    Example:
        >>> print_stage_header(1, 7, "Audio Extraction")
        [Stage 1/7] Audio Extraction
    """
    import click
    click.echo(f"\n[Stage {stage_num}/{total_stages}] {stage_name}")


def print_success_summary(
    final_output: Path,
    processing_time: float,
    stages_completed: int = 7
):
    """
    Print final success summary.

    Args:
        final_output: Path to final output file
        processing_time: Total processing time in seconds
        stages_completed: Number of stages completed

    Example:
        >>> print_success_summary(
        ...     Path("output/final.mp4"),
        ...     125.5,
        ...     7
        ... )
    """
    import click

    click.echo()
    click.secho("✓ Pipeline complete - All stages finished!", fg="green", bold=True)
    click.echo()
    click.echo(f"Final video: {final_output}")

    if final_output.exists():
        file_size = format_file_size(final_output.stat().st_size)
        click.echo(f"File size: {file_size}")

    click.echo(f"Total processing time: {processing_time:.1f}s ({processing_time/60:.1f}min)")
    click.echo(f"Stages completed: {stages_completed}/7")
    click.echo()
    click.secho(f"🎉 Success! Video ready: {final_output}", fg="green", bold=True)
