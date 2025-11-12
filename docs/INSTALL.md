# Installation Guide - HeyGen Social Clipper

> Comprehensive installation instructions for macOS M2, Linux, and Windows

## Table of Contents

- [macOS M1/M2 (Apple Silicon)](#macos-m1m2-apple-silicon)
- [Linux (Ubuntu/Debian)](#linux-ubuntudebian)
- [Windows 11](#windows-11)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## macOS M1/M2 (Apple Silicon)

### Prerequisites

- macOS 13 (Ventura) or later
- Xcode Command Line Tools
- Homebrew package manager

### Step 1: Install Homebrew

If not already installed:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After installation, add Homebrew to your PATH:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### Step 2: Install Python 3.10 or 3.11

**Option A: Using Homebrew (Recommended)**

```bash
# Install Python 3.11
brew install python@3.11

# Verify installation
python3.11 --version
# Should output: Python 3.11.x

# Create symlink (optional)
brew link python@3.11
```

**Option B: Using pyenv (For multiple Python versions)**

```bash
# Install pyenv
brew install pyenv

# Add to shell configuration
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zprofile
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zprofile
echo 'eval "$(pyenv init --path)"' >> ~/.zprofile
echo 'eval "$(pyenv init -)"' >> ~/.zprofile

# Reload shell
source ~/.zprofile

# Install Python 3.11
pyenv install 3.11.6
pyenv global 3.11.6

# Verify
python --version
```

### Step 3: Install FFmpeg with VideoToolbox Support

FFmpeg with VideoToolbox is **critical** for M2 hardware acceleration:

```bash
# Install FFmpeg with all required codecs
brew install ffmpeg

# FFmpeg will automatically include VideoToolbox support on Apple Silicon
```

**Verify FFmpeg Installation:**

```bash
# Check FFmpeg version
ffmpeg -version
# Should show: ffmpeg version 6.x or later

# Verify VideoToolbox encoders are available
ffmpeg -hide_banner -encoders | grep videotoolbox
```

Expected output:
```
V..... h264_videotoolbox    VideoToolbox H.264 Encoder
V..... hevc_videotoolbox    VideoToolbox H.265 Encoder
V..... prores_videotoolbox  VideoToolbox ProRes Encoder
```

**Verify VideoToolbox decoders:**

```bash
ffmpeg -hide_banner -decoders | grep videotoolbox
```

Expected output:
```
V..... h264_vt              VideoToolbox H.264 Decoder
V..... hevc_vt              VideoToolbox H.265/HEVC Decoder
```

### Step 4: Install Additional System Dependencies

```bash
# Install required audio libraries for librosa
brew install libsndfile

# Install git (if not already installed)
brew install git
```

### Step 5: Clone Repository

```bash
# Clone the repository
git clone https://github.com/colehanan1/BrainBinge-Video-Editor.git
cd BrainBinge-Video-Editor

# Checkout the appropriate branch (if needed)
git checkout main
```

### Step 6: Create Virtual Environment

```bash
# Create virtual environment using Python 3.11
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip, setuptools, and wheel
pip install --upgrade pip setuptools wheel
```

### Step 7: Install HeyGen Social Clipper

**For Production Use:**

```bash
# Install production dependencies
pip install -r requirements.txt

# Install package
pip install -e .
```

**For Development:**

```bash
# Install all dependencies (production + development)
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install package with dev extras
pip install -e ".[dev]"
```

**Note on PyTorch Installation:**

The requirements.txt will install PyTorch with MPS (Metal Performance Shaders) support automatically for M1/M2 Macs. If you encounter issues:

```bash
# Manually install PyTorch for M1/M2
pip install torch torchvision torchaudio
```

### Step 8: Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

Required environment variables:
```bash
# Pexels API key (required for B-roll integration)
PEXELS_API_KEY=your_pexels_api_key_here

# Optional: Whisper API key
WHISPER_API_KEY=your_whisper_api_key_here

# Output directories
OUTPUT_DIR=data/output
TEMP_DIR=data/temp
LOG_DIR=logs
```

**Get Pexels API Key:**
1. Visit https://www.pexels.com/api/
2. Sign up for free account
3. Generate API key
4. Add to `.env` file

### Step 9: Initialize Configuration

```bash
# Create necessary directories
make init-config

# Or manually:
mkdir -p config data/input data/output data/temp logs
```

### Step 10: Verify Installation

```bash
# Run environment verification script
make verify

# Or run directly:
python scripts/verify_env.py
```

Expected output:
```
✓ Python version: 3.11.x
✓ FFmpeg installed: 6.x
✓ VideoToolbox H.264 encoder available
✓ VideoToolbox HEVC encoder available
✓ All Python dependencies installed
✓ Pexels API key configured
✓ Environment setup complete!
```

### Step 11: Test Installation

```bash
# Test CLI is accessible
heygen-clipper --version
# Should output: heygen-social-clipper 0.1.0-alpha

# Show available commands
heygen-clipper --help

# Run validation test (if you have sample files)
heygen-clipper validate --config config/brand.yaml
```

### M2-Specific Optimizations

**1. Enable MPS Acceleration for PyTorch:**

```python
import torch
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("Using MPS (Metal Performance Shaders)")
else:
    device = torch.device("cpu")
```

**2. Verify FFmpeg VideoToolbox:**

```bash
# Test H.264 encoding with VideoToolbox
ffmpeg -f lavfi -i testsrc=duration=5:size=1920x1080:rate=30 \
    -c:v h264_videotoolbox -b:v 5M test_videotoolbox.mp4

# Check if file was created successfully
ls -lh test_videotoolbox.mp4

# Clean up test file
rm test_videotoolbox.mp4
```

**3. Performance Tips:**

- Use VideoToolbox for encoding (much faster than software encoding)
- Keep Python 3.11 (best compatibility with PyTorch on M2)
- Allocate sufficient RAM (recommend 16GB minimum)
- Use SSD storage for temp files

---

## Linux (Ubuntu/Debian)

### Prerequisites

- Ubuntu 22.04 LTS or Debian 11+
- sudo access

### Step 1: Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2: Install Python 3.10+

```bash
# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Install pip
sudo apt install -y python3-pip

# Verify
python3.11 --version
```

### Step 3: Install FFmpeg and Dependencies

```bash
# Install FFmpeg with extra codecs
sudo apt install -y ffmpeg libavcodec-extra libavformat-dev libavutil-dev

# Install audio libraries
sudo apt install -y libsndfile1 libsndfile1-dev

# Install build tools (required for some Python packages)
sudo apt install -y build-essential

# Verify FFmpeg
ffmpeg -version
```

### Step 4: Install Git

```bash
sudo apt install -y git
```

### Step 5: Clone Repository

```bash
git clone https://github.com/colehanan1/BrainBinge-Video-Editor.git
cd BrainBinge-Video-Editor
```

### Step 6: Create Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Step 7: Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt
pip install -e .

# Or for development:
pip install -r requirements.txt -r requirements-dev.txt
pip install -e ".[dev]"
```

### Step 8: Configure Environment

```bash
cp .env.example .env
nano .env  # Add your API keys
```

### Step 9: Verify Installation

```bash
python scripts/verify_env.py
```

### GPU Acceleration (NVIDIA Only)

If you have an NVIDIA GPU and want CUDA acceleration:

```bash
# Check CUDA availability
nvidia-smi

# Install PyTorch with CUDA 11.8
pip uninstall torch torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verify CUDA in PyTorch
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

---

## Windows 11

### Prerequisites

- Windows 11 (or Windows 10 build 19041+)
- Administrator access

### Step 1: Install Python 3.10 or 3.11

1. Download Python from https://www.python.org/downloads/
2. Run installer
3. **Important:** Check "Add Python to PATH"
4. Click "Install Now"
5. Verify installation:

```powershell
python --version
```

### Step 2: Install FFmpeg

**Option A: Using winget (Windows 11)**

```powershell
winget install FFmpeg
```

**Option B: Manual Installation**

1. Download FFmpeg from https://ffmpeg.org/download.html#build-windows
2. Extract to `C:\ffmpeg`
3. Add to PATH:
   - Open System Properties → Environment Variables
   - Edit PATH variable
   - Add: `C:\ffmpeg\bin`
4. Verify in new terminal:

```powershell
ffmpeg -version
```

### Step 3: Install Git

Download and install from: https://git-scm.com/download/win

### Step 4: Install Visual C++ Build Tools

Required for some Python packages:

1. Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Run installer
3. Select "Desktop development with C++"
4. Install

### Step 5: Clone Repository

```powershell
git clone https://github.com/colehanan1/BrainBinge-Video-Editor.git
cd BrainBinge-Video-Editor
```

### Step 6: Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate
.\venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip setuptools wheel
```

### Step 7: Install Dependencies

```powershell
# Install requirements
pip install -r requirements.txt
pip install -e .
```

### Step 8: Configure Environment

```powershell
copy .env.example .env
notepad .env  # Add your API keys
```

### Step 9: Verify Installation

```powershell
python scripts\verify_env.py
```

---

## Verification

After installation on any platform, run these verification steps:

### 1. Environment Check

```bash
make env-check
```

### 2. Detailed Verification

```bash
make verify
```

### 3. Test Python Imports

```python
python -c "
import ffmpeg
import pysubs2
import torch
import click
import pydantic
print('All core imports successful!')
"
```

### 4. Test FFmpeg Access

```bash
python -c "
import ffmpeg
probe = ffmpeg.probe('test_file.mp4')  # Will fail if file doesn't exist, but tests import
print('FFmpeg-python working!')
"
```

### 5. Test CLI

```bash
heygen-clipper --help
heygen-clipper --version
```

---

## Troubleshooting

### macOS M2 Issues

#### Issue: `torch` installation fails

**Solution:**
```bash
# Use Python 3.11 (not 3.12)
pyenv install 3.11.6
pyenv global 3.11.6

# Reinstall
pip install --upgrade pip setuptools wheel
pip install torch torchvision torchaudio
```

#### Issue: FFmpeg not found

**Solution:**
```bash
# Ensure Homebrew is in PATH
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zprofile
source ~/.zprofile

# Reinstall FFmpeg
brew reinstall ffmpeg

# Verify
which ffmpeg
```

#### Issue: VideoToolbox not available

**Solution:**
```bash
# Check macOS version (must be 13+)
sw_vers

# Verify FFmpeg build
ffmpeg -hide_banner -encoders | grep videotoolbox

# If missing, reinstall FFmpeg
brew uninstall ffmpeg
brew install ffmpeg
```

#### Issue: `librosa` fails to import

**Solution:**
```bash
# Install soundfile first
pip install soundfile

# Then install librosa
pip install librosa

# Install system audio libraries
brew install libsndfile
```

### Linux Issues

#### Issue: Permission denied errors

**Solution:**
```bash
# Ensure user has proper permissions
sudo chown -R $USER:$USER /path/to/BrainBinge-Video-Editor

# Or use sudo for system-wide install
sudo pip install -e .
```

#### Issue: `soundfile` ImportError

**Solution:**
```bash
# Install libsndfile
sudo apt install libsndfile1

# Reinstall soundfile
pip install --force-reinstall soundfile
```

### Windows Issues

#### Issue: `torch` requires Visual C++ 14.0

**Solution:**
Install Visual C++ Build Tools (see Step 4 above)

#### Issue: FFmpeg not in PATH

**Solution:**
```powershell
# Permanently add to PATH
setx PATH "%PATH%;C:\ffmpeg\bin"

# Restart terminal and verify
ffmpeg -version
```

### General Issues

#### Issue: Out of memory during installation

**Solution:**
```bash
# Install with reduced memory usage
pip install --no-cache-dir -r requirements.txt
```

#### Issue: Conflicting dependencies

**Solution:**
```bash
# Clean install
pip uninstall -r requirements.txt -y
pip cache purge
pip install -r requirements.txt
```

#### Issue: SSL certificate errors

**Solution:**
```bash
# Update certificates
pip install --upgrade certifi

# Or use trusted host (temporary)
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

---

## Post-Installation

### Install Pre-commit Hooks (Development)

```bash
make pre-commit-install
```

### Download Sample Data

```bash
# Create sample directories
mkdir -p data/input data/output data/temp

# Download sample files (if available)
# curl -o data/input/sample_video.mp4 https://example.com/sample.mp4
```

### Run Tests

```bash
# Run all tests
make test

# Run fast tests only
make test-fast

# Run with coverage
make coverage
```

---

## Keeping Up to Date

### Update Dependencies

```bash
# Check for outdated packages
make deps-outdated

# Update to latest compatible versions
pip install -U -r requirements.txt
```

### Update FFmpeg

**macOS:**
```bash
brew upgrade ffmpeg
```

**Linux:**
```bash
sudo apt update && sudo apt upgrade ffmpeg
```

**Windows:**
Download latest version from ffmpeg.org

---

## Support

If you encounter issues not covered in this guide:

1. Check existing issues: https://github.com/colehanan1/BrainBinge-Video-Editor/issues
2. Run diagnostic: `python scripts/verify_env.py --verbose`
3. Create new issue with diagnostic output

**Contact:** support@brainbinge.com

---

**Last Updated:** 2025-11-12
**Version:** 0.1.0-alpha
**Tested On:** macOS 14 (M2), Ubuntu 22.04, Windows 11
