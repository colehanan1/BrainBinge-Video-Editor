"""
Integration Tests for CLI

Tests the complete CLI workflow including validation, processing,
and error handling.

Run with:
    pytest tests/integration/test_cli.py -v
"""

import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile
import shutil

from src.cli import cli


class TestCLIValidation:
    """Test CLI validation command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_validate_missing_files(self):
        """Test validation with missing files."""
        result = self.runner.invoke(cli, [
            'validate',
            '--video', 'nonexistent.mp4',
            '--script', 'nonexistent.txt'
        ])

        assert result.exit_code == 1
        assert 'Validation failed' in result.output
        assert 'not found' in result.output

    def test_validate_invalid_video_format(self, tmp_path):
        """Test validation with invalid video format."""
        # Create a dummy file with invalid extension
        invalid_video = tmp_path / "video.txt"
        invalid_video.write_text("dummy")

        result = self.runner.invoke(cli, [
            'validate',
            '--video', str(invalid_video)
        ])

        assert result.exit_code == 1
        assert 'Unsupported video format' in result.output

    def test_validate_valid_files(self, tmp_path):
        """Test validation with valid files."""
        # Create valid dummy files
        video = tmp_path / "video.mp4"
        script = tmp_path / "script.txt"
        config = tmp_path / "config.yaml"

        video.write_bytes(b'dummy video data')
        script.write_text("This is a test script")
        config.write_text("brand:\n  name: Test Brand")

        result = self.runner.invoke(cli, [
            'validate',
            '--video', str(video),
            '--script', str(script),
            '--config', str(config)
        ])

        assert result.exit_code == 0
        assert 'All validations passed' in result.output


class TestCLIHelp:
    """Test CLI help and version commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_help_command(self):
        """Test --help flag."""
        result = self.runner.invoke(cli, ['--help'])

        assert result.exit_code == 0
        assert 'HeyGen Social Clipper' in result.output
        assert 'process' in result.output
        assert 'validate' in result.output

    def test_version_command(self):
        """Test --version flag."""
        result = self.runner.invoke(cli, ['--version'])

        assert result.exit_code == 0
        assert 'heygen-clipper' in result.output

    def test_process_help(self):
        """Test process command help."""
        result = self.runner.invoke(cli, ['process', '--help'])

        assert result.exit_code == 0
        assert '--video' in result.output
        assert '--script' in result.output
        assert '--config' in result.output


@pytest.mark.integration
@pytest.mark.slow
class TestCLIEndToEnd:
    """
    End-to-end integration tests for the full pipeline.

    These tests require sample video files and may take several minutes.
    Skip with: pytest -m "not slow"
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.sample_dir = Path("data/test_samples/sample_01")

    @pytest.mark.skipif(
        not Path("data/test_samples/sample_01/video.mp4").exists(),
        reason="Sample video not found"
    )
    def test_full_pipeline(self, tmp_path):
        """Test complete 7-stage pipeline."""
        # Prepare paths
        video = self.sample_dir / "video.mp4"
        script = self.sample_dir / "script.txt"
        config = Path("config/brand_example.yaml")
        output = tmp_path / "output"

        # Run full pipeline
        result = self.runner.invoke(cli, [
            'process',
            '--video', str(video),
            '--script', str(script),
            '--config', str(config),
            '--output', str(output)
        ])

        # Check success
        if result.exit_code != 0:
            print(result.output)
            print(result.exception)

        assert result.exit_code == 0
        assert 'Pipeline complete' in result.output

        # Verify outputs exist
        assert (output / "final").exists()
        final_video = list((output / "final").glob("*.mp4"))
        assert len(final_video) > 0
        assert final_video[0].stat().st_size > 0

    def test_pipeline_with_verbose(self, tmp_path):
        """Test pipeline with verbose logging."""
        if not (self.sample_dir / "video.mp4").exists():
            pytest.skip("Sample video not found")

        video = self.sample_dir / "video.mp4"
        script = self.sample_dir / "script.txt"
        config = Path("config/brand_example.yaml")
        output = tmp_path / "output"

        result = self.runner.invoke(cli, [
            '--verbose',
            'process',
            '--video', str(video),
            '--script', str(script),
            '--config', str(config),
            '--output', str(output)
        ])

        # Verbose mode should show more details
        assert 'Stage' in result.output


class TestCLIErrorHandling:
    """Test CLI error handling and recovery."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_missing_required_args(self):
        """Test error when required arguments are missing."""
        result = self.runner.invoke(cli, ['process'])

        assert result.exit_code != 0
        assert 'Error' in result.output or 'required' in result.output.lower()

    def test_invalid_config_file(self, tmp_path):
        """Test error with invalid config file."""
        video = tmp_path / "video.mp4"
        script = tmp_path / "script.txt"
        config = tmp_path / "config.yaml"

        video.write_bytes(b'dummy')
        script.write_text("test")
        config.write_text("invalid: yaml: content: [}")

        result = self.runner.invoke(cli, [
            'validate',
            '--video', str(video),
            '--script', str(script),
            '--config', str(config)
        ])

        # Should fail validation
        assert result.exit_code != 0


@pytest.fixture(scope="session")
def sample_data_dir(tmp_path_factory):
    """
    Create sample data directory for tests.

    This fixture creates minimal test files that can be used
    across multiple tests.
    """
    data_dir = tmp_path_factory.mktemp("sample_data")

    # Create minimal sample files
    (data_dir / "video.mp4").write_bytes(b'dummy video')
    (data_dir / "script.txt").write_text("This is a test script.")
    (data_dir / "config.yaml").write_text("""
brand:
  name: Test Brand
  colors:
    primary: "#FF6B6B"
captions:
  font_size: 28
    """)

    return data_dir


def test_cli_import():
    """Test that CLI can be imported successfully."""
    from src.cli import main
    assert callable(main)


def test_logging_setup():
    """Test that logging utilities work correctly."""
    from src.utils.logging import setup_logging

    logger = setup_logging(verbose=True)
    assert logger is not None

    # Test logging levels
    logger_quiet = setup_logging(quiet=True)
    assert logger_quiet is not None


def test_validation_helpers():
    """Test validation helper functions."""
    from src.utils.cli_helpers import validate_inputs
    from pathlib import Path

    # Test with nonexistent files
    errors = validate_inputs(
        video_path=Path("nonexistent.mp4"),
        script_path=Path("nonexistent.txt")
    )

    assert len(errors) > 0
    assert any('not found' in err.lower() for err in errors)


def test_config_loader():
    """Test configuration loader."""
    from src.utils.config_loader import _inject_env_vars
    import os

    # Set test environment variable
    os.environ['PEXELS_API_KEY'] = 'test_key_12345'

    config = {'pexels': {}}
    config = _inject_env_vars(config)

    assert config['pexels']['api_key'] == 'test_key_12345'

    # Cleanup
    del os.environ['PEXELS_API_KEY']
