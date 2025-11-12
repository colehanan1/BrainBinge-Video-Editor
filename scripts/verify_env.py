#!/usr/bin/env python3
"""
Environment Verification Script for HeyGen Social Clipper

Checks all dependencies, system requirements, and configuration to ensure
the development environment is properly set up.

Usage:
    python scripts/verify_env.py
    python scripts/verify_env.py --verbose
    make verify
"""

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str) -> None:
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"  {text}")


def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is >= 3.10."""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version.major == 3 and version.minor >= 10:
        return True, version_str
    return False, version_str


def check_command_exists(command: str) -> Tuple[bool, str]:
    """Check if a command exists in PATH."""
    try:
        result = subprocess.run(
            [command, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        # Extract version from output
        version = result.stdout.split('\n')[0] if result.returncode == 0 else "unknown"
        return result.returncode == 0, version
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "not found"


def check_ffmpeg_capabilities() -> Tuple[List[str], List[str]]:
    """Check FFmpeg encoders and decoders."""
    encoders = []
    decoders = []

    try:
        # Check encoders
        result = subprocess.run(
            ['ffmpeg', '-hide_banner', '-encoders'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if 'videotoolbox' in result.stdout:
            if 'h264_videotoolbox' in result.stdout:
                encoders.append('h264_videotoolbox')
            if 'hevc_videotoolbox' in result.stdout:
                encoders.append('hevc_videotoolbox')
            if 'prores_videotoolbox' in result.stdout:
                encoders.append('prores_videotoolbox')
        elif 'nvenc' in result.stdout:
            if 'h264_nvenc' in result.stdout:
                encoders.append('h264_nvenc')
            if 'hevc_nvenc' in result.stdout:
                encoders.append('hevc_nvenc')
        else:
            encoders.append('libx264 (software)')

        # Check decoders
        result = subprocess.run(
            ['ffmpeg', '-hide_banner', '-decoders'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if '_vt' in result.stdout or 'videotoolbox' in result.stdout:
            decoders.append('VideoToolbox')
        elif 'cuvid' in result.stdout:
            decoders.append('NVDEC (CUDA)')
        else:
            decoders.append('software')

    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return encoders, decoders


def check_python_package(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """Check if a Python package is installed."""
    if import_name is None:
        import_name = package_name

    try:
        module = __import__(import_name)
        version = getattr(module, '__version__', 'unknown')
        return True, version
    except ImportError:
        return False, "not installed"


def check_env_file() -> Tuple[bool, List[str]]:
    """Check if .env file exists and has required variables."""
    env_path = Path('.env')

    if not env_path.exists():
        return False, []

    missing_vars = []
    required_vars = ['PEXELS_API_KEY']

    with open(env_path, 'r') as f:
        content = f.read()
        for var in required_vars:
            if var not in content or f'{var}=your_' in content or f'{var}=' == content.split(var)[1].split('\n')[0]:
                missing_vars.append(var)

    return True, missing_vars


def check_directories() -> List[str]:
    """Check if required directories exist."""
    required_dirs = ['src', 'tests', 'data', 'config', 'logs']
    missing_dirs = []

    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            missing_dirs.append(dir_name)

    return missing_dirs


def check_gpu_availability() -> Tuple[str, List[str]]:
    """Check for GPU availability (MPS for M1/M2, CUDA for NVIDIA)."""
    gpu_type = "None"
    details = []

    try:
        import torch

        if torch.backends.mps.is_available():
            gpu_type = "Apple MPS (Metal)"
            details.append("Metal Performance Shaders available")
            if torch.backends.mps.is_built():
                details.append("MPS backend built into PyTorch")
        elif torch.cuda.is_available():
            gpu_type = f"NVIDIA CUDA {torch.version.cuda}"
            details.append(f"CUDA devices: {torch.cuda.device_count()}")
            if torch.cuda.device_count() > 0:
                details.append(f"Primary GPU: {torch.cuda.get_device_name(0)}")
        else:
            gpu_type = "CPU only"
            details.append("No GPU acceleration available")

    except ImportError:
        gpu_type = "PyTorch not installed"

    return gpu_type, details


def main():
    """Run all environment checks."""
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    all_checks_passed = True

    print(f"\n{Colors.BOLD}HeyGen Social Clipper - Environment Verification{Colors.END}")
    print(f"Platform: {platform.system()} {platform.release()} ({platform.machine()})")

    # Check Python version
    print_header("Python Environment")
    python_ok, python_version = check_python_version()
    if python_ok:
        print_success(f"Python version: {python_version}")
    else:
        print_error(f"Python version: {python_version} (requires >= 3.10)")
        all_checks_passed = False

    # Check system commands
    print_header("System Commands")

    # FFmpeg
    ffmpeg_ok, ffmpeg_version = check_command_exists('ffmpeg')
    if ffmpeg_ok:
        print_success(f"FFmpeg installed: {ffmpeg_version}")

        # Check FFmpeg capabilities
        encoders, decoders = check_ffmpeg_capabilities()
        if encoders:
            print_info(f"Hardware encoders: {', '.join(encoders)}")
        if decoders:
            print_info(f"Hardware decoders: {', '.join(decoders)}")

        # Warn if no hardware acceleration on macOS
        if platform.system() == 'Darwin' and 'videotoolbox' not in str(encoders):
            print_warning("VideoToolbox not available - reinstall FFmpeg via Homebrew")
            all_checks_passed = False
    else:
        print_error("FFmpeg not found in PATH")
        all_checks_passed = False

    # Git
    git_ok, git_version = check_command_exists('git')
    if git_ok:
        print_success(f"Git installed: {git_version}")
    else:
        print_warning("Git not found (optional for runtime)")

    # Check core Python packages
    print_header("Core Python Dependencies")

    core_packages = [
        ('ffmpeg-python', 'ffmpeg'),
        ('pysubs2', 'pysubs2'),
        ('torch', 'torch'),
        ('torchaudio', 'torchaudio'),
        ('transformers', 'transformers'),
        ('librosa', 'librosa'),
        ('soundfile', 'soundfile'),
        ('Pillow', 'PIL'),
        ('numpy', 'numpy'),
        ('scipy', 'scipy'),
        ('Click', 'click'),
        ('PyYAML', 'yaml'),
        ('pydantic', 'pydantic'),
        ('requests', 'requests'),
    ]

    missing_packages = []
    for package_name, import_name in core_packages:
        package_ok, package_version = check_python_package(package_name, import_name)
        if package_ok:
            if verbose:
                print_success(f"{package_name}: {package_version}")
        else:
            print_error(f"{package_name}: not installed")
            missing_packages.append(package_name)
            all_checks_passed = False

    if not verbose and not missing_packages:
        print_success(f"All {len(core_packages)} core dependencies installed")

    # Check GPU availability
    print_header("GPU/Hardware Acceleration")
    gpu_type, gpu_details = check_gpu_availability()

    if "MPS" in gpu_type:
        print_success(f"GPU: {gpu_type}")
        for detail in gpu_details:
            print_info(detail)
    elif "CUDA" in gpu_type:
        print_success(f"GPU: {gpu_type}")
        for detail in gpu_details:
            print_info(detail)
    elif "CPU only" in gpu_type:
        print_warning("GPU: CPU only (no hardware acceleration)")
        print_info("Video processing will be slower")
    else:
        print_error(f"GPU check failed: {gpu_type}")

    # Check environment configuration
    print_header("Environment Configuration")

    env_exists, missing_vars = check_env_file()
    if env_exists:
        if not missing_vars:
            print_success(".env file configured")
        else:
            print_warning(f".env file exists but missing: {', '.join(missing_vars)}")
            print_info("Add your API keys to .env file")
    else:
        print_warning(".env file not found")
        print_info("Copy .env.example to .env and add your API keys")

    # Check directories
    missing_dirs = check_directories()
    if not missing_dirs:
        print_success("All required directories exist")
    else:
        print_warning(f"Missing directories: {', '.join(missing_dirs)}")
        print_info("Run: make init-config")

    # Check optional dev dependencies
    if verbose:
        print_header("Development Dependencies (Optional)")

        dev_packages = [
            ('pytest', 'pytest'),
            ('black', 'black'),
            ('mypy', 'mypy'),
            ('ruff', 'ruff'),
        ]

        for package_name, import_name in dev_packages:
            package_ok, package_version = check_python_package(package_name, import_name)
            if package_ok:
                print_success(f"{package_name}: {package_version}")
            else:
                print_warning(f"{package_name}: not installed (dev dependency)")

    # Test imports
    print_header("Import Tests")

    try:
        from src import __version__
        print_success(f"Package import successful (version {__version__})")
    except ImportError as e:
        print_error(f"Cannot import package: {e}")
        print_info("Run: pip install -e .")
        all_checks_passed = False

    # Final summary
    print_header("Summary")

    if all_checks_passed:
        print_success("Environment setup complete!")
        print_info("You're ready to start development")
        print_info("\nNext steps:")
        print_info("  1. Add API keys to .env file")
        print_info("  2. Run tests: make test")
        print_info("  3. Start developing: heygen-clipper --help")
        return 0
    else:
        print_error("Some checks failed")
        print_info("\nTo fix issues:")
        print_info("  1. Install missing dependencies: pip install -r requirements.txt")
        print_info("  2. Install FFmpeg: brew install ffmpeg (macOS)")
        print_info("  3. Create .env file: cp .env.example .env")
        print_info("  4. Install package: pip install -e .")
        print_info("\nFor detailed installation instructions:")
        print_info("  See docs/INSTALL.md")
        return 1


if __name__ == '__main__':
    sys.exit(main())
