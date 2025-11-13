"""
CLI Entry Point for HeyGen Social Clipper

Provides command-line interface for video processing operations using Click framework.

Commands:
    process     - Process a single video
    batch       - Process multiple videos
    watch       - Watch directory for new videos
    webhook     - Start webhook server for Make.com integration
    validate    - Validate configuration and input files
    config      - Manage configuration files

Example:
    $ heygen-clipper process --video input.mp4 --script script.txt --config brand.yaml
    $ heygen-clipper webhook --port 8000 --config brand.yaml
"""

from pathlib import Path
from typing import Optional

import click

from src import __version__


@click.group()
@click.version_option(version=__version__, prog_name="heygen-clipper")
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose logging"
)
@click.option(
    "--quiet", "-q", is_flag=True, help="Suppress non-error output"
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool) -> None:
    """
    HeyGen Social Clipper - Transform AI videos into viral social content.

    Transform HeyGen videos into platform-optimized social media content with
    synchronized captions, B-roll integration, and brand styling.
    """
    # TODO: Initialize logging based on verbose/quiet flags
    # TODO: Store context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet


@cli.command()
@click.option(
    "--video",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to HeyGen video file (MP4)",
)
@click.option(
    "--script",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to script file (TXT, JSON, or CSV)",
)
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to brand configuration (YAML or JSON)",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    required=True,
    help="Output directory for processed videos",
)
@click.option(
    "--platform",
    type=click.Choice(["instagram", "tiktok", "youtube", "all"]),
    default="all",
    help="Target platform(s) for export",
)
@click.option(
    "--broll-plan",
    type=click.Path(exists=True, path_type=Path),
    required=False,
    help="Path to B-roll plan CSV (optional, defaults to sample_broll_plan.csv)",
)
@click.pass_context
def process(
    ctx: click.Context,
    video: Path,
    script: Path,
    config: Path,
    output: Path,
    platform: str,
    broll_plan: Path = None,
) -> None:
    """
    Process a single HeyGen video into social media content.

    Runs the complete 7-stage pipeline to transform the input video
    with captions, B-roll, and platform-specific optimizations.

    Example:
        $ heygen-clipper process \\
            --video data/input/video.mp4 \\
            --script data/input/script.txt \\
            --config config/brand.yaml \\
            --output data/output
    """
    import sys
    from src.config import ConfigLoader
    from src.modules.audio import AudioExtractor

    click.echo(f"Processing video: {video}")
    click.echo(f"Using script: {script}")
    click.echo(f"Configuration: {config}")
    click.echo(f"Output directory: {output}")
    click.echo(f"Target platform: {platform}")
    click.echo()

    try:
        # Load configuration
        click.echo("Loading configuration...")
        cfg = ConfigLoader.load(config)

        # Create output directories
        output_path = Path(output)
        audio_dir = output_path / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Stage 1: Audio Extraction
        click.echo("\n[Stage 1/7] Extracting audio...")
        audio_extractor = AudioExtractor(cfg)
        audio_output = audio_dir / f"{video.stem}.wav"

        result = audio_extractor.process(video, audio_output)

        if result.success:
            click.secho(f"✓ Audio extracted: {audio_output}", fg="green")
            click.echo(f"  Duration: {result.metadata.get('duration', 'unknown')}s")
            click.echo(f"  Sample rate: {result.metadata.get('sample_rate', 'unknown')}Hz")
            click.echo(f"  Channels: {result.metadata.get('channels', 'unknown')}")
            click.echo(f"  Normalized: {result.metadata.get('normalized', False)}")
            click.echo(f"  Sync valid: {result.metadata.get('sync_valid', 'unknown')}")
        else:
            click.secho(f"✗ Audio extraction failed", fg="red")
            sys.exit(1)

        # Stage 2: Force Alignment
        click.echo("\n[Stage 2/7] Force Alignment")
        from src.modules.alignment import ForceAligner

        aligner = ForceAligner(cfg)
        alignment_dir = output_path / "alignment"
        alignment_dir.mkdir(parents=True, exist_ok=True)
        alignment_output = alignment_dir / f"{video.stem}.json"

        result = aligner.process(audio_output, alignment_output, script)

        if result.success:
            click.secho(f"✓ Alignment complete: {alignment_output}", fg="green")
            click.echo(f"  Word count: {result.metadata.get('word_count', 0)}")
            click.echo(f"  Expected words: {result.metadata.get('expected_words', 0)}")
            click.echo(f"  Coverage: {result.metadata.get('coverage', 0):.1%}")
            click.echo(f"  Processing time: {result.metadata.get('processing_time', 0):.1f}s")
            click.echo(f"  Gap smoothing: {'enabled' if result.metadata.get('smoothed') else 'disabled'}")
        else:
            click.secho(f"✗ Force alignment failed", fg="red")
            sys.exit(1)

        # Stage 3: Caption Generation
        click.echo("\n[Stage 3/7] Caption Generation")
        from src.modules.captions import CaptionGenerator

        caption_generator = CaptionGenerator(cfg)
        captions_dir = output_path / "captions"
        captions_dir.mkdir(parents=True, exist_ok=True)
        captions_output = captions_dir / f"{video.stem}.srt"

        result = caption_generator.process(alignment_output, captions_output)

        if result.success:
            click.secho(f"✓ Captions generated: {captions_output}", fg="green")
            click.echo(f"  Caption count: {result.metadata.get('caption_count', 0)}")
            click.echo(f"  Total duration: {result.metadata.get('total_duration', 0):.1f}s")
            click.echo(f"  Avg duration: {result.metadata.get('avg_duration_ms', 0):.0f}ms per caption")
            click.echo(f"  Processing time: {result.metadata.get('processing_time', 0):.2f}s")
            click.echo(f"  Short word merging: {'enabled' if result.metadata.get('merged') else 'disabled'}")
        else:
            click.secho(f"✗ Caption generation failed", fg="red")
            sys.exit(1)

        # Stage 4: Caption Styling
        click.echo("\n[Stage 4/7] Caption Styling")
        from src.modules.styling import CaptionStyler

        styler = CaptionStyler(cfg)
        styled_dir = output_path / "styled"
        styled_dir.mkdir(parents=True, exist_ok=True)
        styled_output = styled_dir / f"{video.stem}.ass"

        result = styler.process(captions_output, styled_output)

        if result.success:
            click.secho(f"✓ Captions styled: {styled_output}", fg="green")
            click.echo(f"  Caption count: {result.metadata.get('caption_count', 0)}")
            click.echo(f"  Video resolution: {result.metadata.get('video_resolution', 'unknown')}")
            click.echo(f"  Font: {result.metadata.get('font', 'unknown')}")
            click.echo(f"  Processing time: {result.metadata.get('processing_time', 0):.2f}s")
        else:
            click.secho(f"✗ Caption styling failed", fg="red")
            sys.exit(1)

        # Stage 5: B-roll Integration
        click.echo("\n[Stage 5/7] B-roll Integration")

        # Check for B-roll plan CSV (optional)
        if broll_plan is None:
            broll_plan = Path("data/input/sample_broll_plan.csv")

        broll_output = None

        if broll_plan.exists():
            from src.modules.broll import BRollIntegrator

            integrator = BRollIntegrator(cfg)
            broll_dir = output_path / "broll"
            broll_dir.mkdir(parents=True, exist_ok=True)
            broll_output = broll_dir / f"{video.stem}_clips.json"

            result = integrator.process(broll_plan, broll_output)

            if result.success:
                click.secho(f"✓ B-roll downloaded: {broll_output}", fg="green")
                click.echo(f"  Total clips: {result.metadata.get('clip_count', 0)}")
                click.echo(f"  Downloaded: {result.metadata.get('downloaded_count', 0)}")
                click.echo(f"  Success rate: {result.metadata.get('success_rate', 0):.1f}%")
                click.echo(f"  Failed: {result.metadata.get('failed_count', 0)}")
                click.echo(f"  Processing time: {result.metadata.get('processing_time', 0):.1f}s")
            else:
                error_msg = result.metadata.get('error', 'Unknown error')
                click.secho(f"⚠ B-roll download incomplete: {error_msg}", fg="yellow")
                if 'PEXELS_API_KEY' in error_msg:
                    click.echo("  Tip: Set PEXELS_API_KEY environment variable")
                # Don't exit - continue without B-roll
        else:
            click.secho(f"⚠ B-roll plan not found: {broll_plan}", fg="yellow")
            click.echo("  Skipping B-roll integration (optional)")

        # Stages 6-7: Not yet implemented
        click.echo("\n[Stage 6/7] Video Composition - NOT IMPLEMENTED")
        click.echo("[Stage 7/7] Video Encoding - NOT IMPLEMENTED")

        click.echo()
        click.secho("⚠ Pipeline incomplete - Stages 1-5 implemented, 6-7 remaining", fg="yellow")
        click.echo(f"\nOutputs:")
        click.echo(f"  Audio: {audio_output}")
        click.echo(f"  Alignment: {alignment_output}")
        click.echo(f"  Captions (SRT): {captions_output}")
        click.echo(f"  Styled (ASS): {styled_output}")
        if broll_output and broll_output.exists():
            click.echo(f"  B-roll: {broll_output}")

    except Exception as e:
        click.secho(f"\n✗ Error: {e}", fg="red")
        if ctx.obj.get("verbose"):
            import traceback
            click.echo(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.option(
    "--input-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Directory containing videos and scripts",
)
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to brand configuration",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    required=True,
    help="Output directory for processed videos",
)
@click.option(
    "--workers",
    type=int,
    default=1,
    help="Number of parallel processing workers",
)
@click.pass_context
def batch(
    ctx: click.Context,
    input_dir: Path,
    config: Path,
    output_dir: Path,
    workers: int,
) -> None:
    """
    Process multiple videos in batch mode.

    Processes all videos in the input directory, matching each video
    with its corresponding script file (same basename).

    Example:
        $ heygen-clipper batch \\
            --input-dir data/input \\
            --config config/brand.yaml \\
            --output-dir data/output \\
            --workers 4
    """
    # TODO: Implement batch processing logic
    # TODO: Use multiprocessing for parallel execution
    # TODO: Progress bar with tqdm
    click.echo(f"Batch processing directory: {input_dir}")
    click.echo(f"Workers: {workers}")


@cli.command()
@click.option(
    "--watch-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Directory to monitor for new files",
)
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to brand configuration",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    required=True,
    help="Output directory",
)
@click.option(
    "--poll-interval",
    type=int,
    default=5,
    help="Polling interval in seconds",
)
@click.pass_context
def watch(
    ctx: click.Context,
    watch_dir: Path,
    config: Path,
    output_dir: Path,
    poll_interval: int,
) -> None:
    """
    Watch directory and auto-process new videos.

    Monitors a directory for new video files and automatically processes
    them when they appear.

    Example:
        $ heygen-clipper watch \\
            --watch-dir /path/to/incoming \\
            --config config/brand.yaml \\
            --output-dir data/output
    """
    # TODO: Implement file system watching (watchdog library)
    # TODO: Debounce file events
    # TODO: Auto-process on new video arrival
    click.echo(f"Watching directory: {watch_dir}")
    click.echo(f"Poll interval: {poll_interval}s")


@cli.command()
@click.option(
    "--host",
    type=str,
    default="0.0.0.0",
    help="Server host address",
)
@click.option(
    "--port",
    type=int,
    default=8000,
    help="Server port",
)
@click.option(
    "--secret",
    type=str,
    envvar="WEBHOOK_SECRET",
    help="Webhook authentication secret",
)
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to brand configuration",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    required=True,
    help="Output directory",
)
@click.pass_context
def webhook(
    ctx: click.Context,
    host: str,
    port: int,
    secret: Optional[str],
    config: Path,
    output_dir: Path,
) -> None:
    """
    Start webhook server for Make.com integration.

    Starts an HTTP server that accepts webhook requests from Make.com
    to process videos automatically.

    Example:
        $ heygen-clipper webhook \\
            --port 8000 \\
            --secret $WEBHOOK_SECRET \\
            --config config/brand.yaml \\
            --output-dir data/output
    """
    # TODO: Implement Flask/FastAPI webhook server
    # TODO: Authenticate requests using secret
    # TODO: Queue processing jobs
    # TODO: Return job status and results
    click.echo(f"Starting webhook server at {host}:{port}")


@cli.command()
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Validate configuration file",
)
@click.option(
    "--script",
    type=click.Path(exists=True, path_type=Path),
    help="Validate script file",
)
@click.option(
    "--video",
    type=click.Path(exists=True, path_type=Path),
    help="Validate video file",
)
@click.pass_context
def validate(
    ctx: click.Context,
    config: Optional[Path],
    script: Optional[Path],
    video: Optional[Path],
) -> None:
    """
    Validate configuration and input files.

    Checks file formats, schema compliance, and required fields
    without processing the video.

    Example:
        $ heygen-clipper validate --config config/brand.yaml
        $ heygen-clipper validate --script script.txt --video video.mp4
    """
    # TODO: Implement validation logic
    # TODO: Use JSON schema for config validation
    # TODO: Check video codec, resolution, frame rate
    # TODO: Parse and validate script format
    if config:
        click.echo(f"Validating config: {config}")
    if script:
        click.echo(f"Validating script: {script}")
    if video:
        click.echo(f"Validating video: {video}")


@cli.group()
def config() -> None:
    """Manage configuration files."""
    pass


@config.command(name="init")
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default="config/brand.yaml",
    help="Output path for configuration file",
)
@click.option(
    "--format",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Configuration file format",
)
def config_init(output: Path, format: str) -> None:
    """
    Generate template configuration file.

    Example:
        $ heygen-clipper config init --output mybrand.yaml
    """
    # TODO: Generate template config from schema
    click.echo(f"Creating config template: {output}")


@config.command(name="show")
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Configuration file to display",
)
def config_show(config: Path) -> None:
    """
    Display current configuration.

    Example:
        $ heygen-clipper config show --config brand.yaml
    """
    # TODO: Load and pretty-print configuration
    click.echo(f"Configuration: {config}")


def main() -> None:
    """Main entry point for CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
