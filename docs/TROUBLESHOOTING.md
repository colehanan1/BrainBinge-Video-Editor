# Troubleshooting Guide - HeyGen Social Clipper

> Quick fixes for common installation and runtime issues

## Table of Contents

- [Installation Issues](#installation-issues)
  - [Python Version Conflicts (pyenv vs conda)](#python-version-conflicts-pyenv-vs-conda)
  - [Package Directory Errors](#package-directory-errors)
  - [Dependency Version Conflicts](#dependency-version-conflicts)
- [FFmpeg Issues](#ffmpeg-issues)
- [PyTorch / GPU Issues](#pytorch--gpu-issues)
- [Runtime Issues](#runtime-issues)

---

## Installation Issues

### Python Version Conflicts (pyenv vs conda)

**Problem**: When you create a conda environment with Python 3.11, but `python --version` shows Python 3.8 from pyenv.

**Symptoms**:
```bash
conda create -n BrainBinge python=3.11
conda activate BrainBinge
python -V
# Shows: Python 3.8.10 (from pyenv instead of conda)
```

**Root Cause**: pyenv shims take precedence over conda in your PATH.

**Solution 1: Temporarily Disable pyenv (Recommended)**

```bash
# Deactivate any conda env first
conda deactivate

# Comment out pyenv in your shell config
# For zsh (macOS default):
nano ~/.zshrc
# Comment out these lines by adding # at the beginning:
# export PYENV_ROOT="$HOME/.pyenv"
# export PATH="$PYENV_ROOT/bin:$PATH"
# eval "$(pyenv init --path)"
# eval "$(pyenv init -)"

# Reload shell
source ~/.zshrc

# Now recreate conda environment
conda create -n BrainBinge python=3.11 pip -y
conda activate BrainBinge

# Verify Python version
python -V  # Should show: Python 3.11.x
which python  # Should show: /Users/your-username/miniconda/envs/BrainBinge/bin/python
```

**Solution 2: Use Conda's Python Explicitly**

```bash
# Activate conda environment
conda activate BrainBinge

# Use conda's Python directly (bypasses pyenv)
/Users/your-username/miniconda/envs/BrainBinge/bin/python -V
# Should show: Python 3.11.14

# Install using conda's Python
/Users/your-username/miniconda/envs/BrainBinge/bin/python -m pip install -U pip setuptools wheel
/Users/your-username/miniconda/envs/BrainBinge/bin/python -m pip install -r requirements.txt
/Users/your-username/miniconda/envs/BrainBinge/bin/python -m pip install -e .
```

**Solution 3: Fix PATH Order**

```bash
# Edit shell configuration
nano ~/.zshrc  # or ~/.bash_profile for bash

# Move conda initialization BEFORE pyenv initialization
# Make sure these lines appear in this order:

# >>> conda initialize >>>
# ... conda init code ...
# <<< conda initialize <<<

# >>> pyenv initialize >>>
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
# <<< pyenv initialize <<<

# Reload shell
source ~/.zshrc

# Verify order
conda activate BrainBinge
which python  # Should now show conda's Python
```

**Solution 4: Use pyenv to Set Python 3.11 (Alternative)**

If you prefer using pyenv over conda:

```bash
# Deactivate conda
conda deactivate

# Install Python 3.11 via pyenv
pyenv install 3.11.7
pyenv global 3.11.7

# Verify
python -V  # Should show: Python 3.11.7

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -U pip setuptools wheel
pip install -r requirements.txt -r requirements-dev.txt
pip install -e ".[dev]"
```

---

### Package Directory Errors

**Problem**: `error: package directory 'src/src' does not exist`

**Symptoms**:
```bash
pip install -e .
# Error: package directory 'src/src' does not exist
```

**Root Cause**: Incorrect `package-dir` configuration in `pyproject.toml` or `setup.py`.

**Solution**: This has been fixed in the latest commit. Pull the latest changes:

```bash
git pull origin claude/bootstrap-heygen-clipper-repo-011CV3EWyqLhoYJM5k846hgu

# Verify the fix in pyproject.toml:
grep -A2 "\[tool.setuptools\]" pyproject.toml
# Should show:
# [tool.setuptools]
# package-dir = {"" = "src"}
# packages = ["cli", "config", "pipeline", "core", "modules", "utils", "api"]

# Try installation again
pip install -e .
```

---

### Dependency Version Conflicts

**Problem**: `ERROR: No matching distribution found for scipy<2.0.0,>=1.11.0`

**Symptoms**:
```bash
pip install -r requirements.txt
# ERROR: No matching distribution found for scipy>=1.11.0
```

**Root Cause**:
- scipy>=1.11.0 requires Python 3.9+
- You're using Python 3.8.x

**Solution**: Upgrade to Python 3.10 or 3.11 (see [Python Version Conflicts](#python-version-conflicts-pyenv-vs-conda) above)

**Quick Check**:
```bash
python -V
# Must show: Python 3.10.x or 3.11.x or 3.12.x
```

---

## FFmpeg Issues

### FFmpeg Not Found

**Problem**: `FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'`

**Solution for macOS**:
```bash
# Install FFmpeg
brew install ffmpeg

# Verify installation
ffmpeg -version

# Ensure FFmpeg is in PATH
which ffmpeg
# Should output: /opt/homebrew/bin/ffmpeg

# If not in PATH, add to shell config:
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Solution for Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install -y ffmpeg

# Verify
ffmpeg -version
```

**Solution for Windows**:
```powershell
# Using winget
winget install FFmpeg

# Or download manually from https://ffmpeg.org/download.html
# Extract to C:\ffmpeg
# Add C:\ffmpeg\bin to PATH
```

---

### VideoToolbox Not Available (macOS M2)

**Problem**: FFmpeg doesn't show VideoToolbox encoders

**Check**:
```bash
ffmpeg -hide_banner -encoders | grep videotoolbox
# Should show:
# V..... h264_videotoolbox
# V..... hevc_videotoolbox
```

**Solution**:
```bash
# Reinstall FFmpeg from Homebrew (includes VideoToolbox on M1/M2)
brew uninstall ffmpeg
brew install ffmpeg

# Verify VideoToolbox support
ffmpeg -hide_banner -encoders | grep videotoolbox

# If still missing, check macOS version (requires macOS 13+)
sw_vers
# ProductVersion should be 13.0 or higher
```

---

## PyTorch / GPU Issues

### MPS Not Available (macOS M2)

**Problem**: `torch.backends.mps.is_available()` returns `False`

**Check**:
```bash
python -c "import torch; print('MPS Available:', torch.backends.mps.is_available())"
```

**Solution**:
```bash
# Ensure you're using Python 3.10 or 3.11 (not 3.12)
python -V

# Reinstall PyTorch with MPS support
pip uninstall torch torchaudio
pip install torch>=2.1.0,<2.3.0 torchaudio>=2.1.0,<2.3.0

# Verify MPS
python -c "import torch; print('MPS Available:', torch.backends.mps.is_available())"
# Should print: MPS Available: True
```

---

### CUDA Not Available (Linux/Windows with NVIDIA GPU)

**Problem**: `torch.cuda.is_available()` returns `False`

**Check**:
```bash
# Verify NVIDIA driver
nvidia-smi

# Check PyTorch CUDA
python -c "import torch; print('CUDA Available:', torch.cuda.is_available())"
```

**Solution**:
```bash
# Uninstall CPU-only PyTorch
pip uninstall torch torchaudio

# Install PyTorch with CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Or for CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Verify
python -c "import torch; print('CUDA Available:', torch.cuda.is_available())"
# Should print: CUDA Available: True
```

---

## Runtime Issues

### ImportError: No module named 'cli'

**Problem**: After installation, CLI command fails

**Symptoms**:
```bash
heygen-clipper --version
# ModuleNotFoundError: No module named 'cli'
```

**Solution**:
```bash
# Reinstall in editable mode
pip uninstall heygen-social-clipper -y
pip install -e .

# Verify installation
pip list | grep heygen
# Should show: heygen-social-clipper  0.1.0a0  /path/to/BrainBinge-Video-Editor

# Test CLI
heygen-clipper --help
```

---

### API Key Not Found

**Problem**: `KeyError: 'PEXELS_API_KEY'`

**Solution**:
```bash
# Check .env file exists
ls -la .env

# If not, create from example
cp .env.example .env

# Edit .env and add your API keys
nano .env

# Add this line:
PEXELS_API_KEY=your_actual_api_key_here

# Verify environment loading
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Pexels Key:', os.getenv('PEXELS_API_KEY'))"
```

**Get Pexels API Key**:
1. Visit https://www.pexels.com/api/
2. Sign up (free)
3. Generate API key
4. Add to `.env` file

---

### Permission Denied Errors (Linux)

**Problem**: `PermissionError: [Errno 13] Permission denied`

**Solution**:
```bash
# Fix file ownership
sudo chown -R $USER:$USER /path/to/BrainBinge-Video-Editor

# Fix directory permissions
chmod -R 755 data/ logs/

# Create directories if missing
mkdir -p data/input data/output data/temp logs

# Try installation again
pip install -e .
```

---

## Complete Clean Reinstall

If all else fails, start fresh:

```bash
# Navigate to project directory
cd /path/to/BrainBinge-Video-Editor

# Pull latest changes
git pull origin claude/bootstrap-heygen-clipper-repo-011CV3EWyqLhoYJM5k846hgu

# Remove old virtual environment
conda deactivate  # or: deactivate
conda env remove -n BrainBinge -y
# or for venv: rm -rf venv

# Temporarily disable pyenv (macOS/Linux)
# Comment out pyenv in ~/.zshrc or ~/.bash_profile
nano ~/.zshrc
# Add # before pyenv lines, then:
source ~/.zshrc

# Create fresh conda environment with Python 3.11
conda create -n BrainBinge python=3.11 pip -y
conda activate BrainBinge

# Verify Python
python -V  # MUST show: Python 3.11.x
which python  # MUST show conda path, NOT pyenv

# Upgrade pip
python -m pip install --upgrade pip setuptools wheel

# Install dependencies
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m pip install -e ".[dev]"

# Verify installation
python scripts/verify_env.py

# Test CLI
heygen-clipper --version
heygen-clipper --help
```

---

## Getting Help

If issues persist:

1. **Run Diagnostic**:
   ```bash
   python scripts/verify_env.py --verbose > diagnostic.txt
   ```

2. **Check Python Environment**:
   ```bash
   python -V
   which python
   pip list > installed_packages.txt
   ```

3. **Check FFmpeg**:
   ```bash
   ffmpeg -version > ffmpeg_info.txt
   ```

4. **Create GitHub Issue**:
   - Visit: https://github.com/colehanan1/BrainBinge-Video-Editor/issues
   - Attach: `diagnostic.txt`, `installed_packages.txt`, `ffmpeg_info.txt`
   - Describe: What you were trying to do, what error occurred

5. **Contact Support**: support@brainbinge.com

---

**Last Updated**: 2025-11-12
**Version**: 0.1.0-alpha
