# Troubleshooting Guide - HeyGen Social Clipper

> Quick fixes for common installation and runtime issues

## Table of Contents

- [TorchAudio FFmpeg Extension Warnings](#torchaudio-ffmpeg-extension-warnings) ⭐ NEW
- [Installation Issues](#installation-issues)
  - [Python Version Conflicts (pyenv vs conda)](#python-version-conflicts-pyenv-vs-conda)
  - [Package Directory Errors](#package-directory-errors)
  - [Dependency Version Conflicts](#dependency-version-conflicts)
- [FFmpeg Issues](#ffmpeg-issues)
- [PyTorch / GPU Issues](#pytorch--gpu-issues)
- [Runtime Issues](#runtime-issues)

---

## TorchAudio FFmpeg Extension Warnings

### Symptoms

When running with `--verbose`, you see DEBUG warnings like:

```
14:59:01 DEBUG    Loading FFmpeg6
14:59:01 DEBUG    Failed to load FFmpeg6 extension.
Traceback (most recent call last):
  ...
OSError: dlopen(...): Library not loaded: @rpath/libavutil.58.dylib
  Reason: tried: '/usr/local/lib/libavutil.58.dylib' (no such file), ...
```

Similar errors appear for FFmpeg5, FFmpeg4, and finally "FFmpeg extension is not available."

### Why This Happens

TorchAudio's `torio` library tries to load FFmpeg extensions for multiple versions (4, 5, 6), but your system has **FFmpeg 8.0** installed via Homebrew. The library paths don't match what `torio` expects internally.

### Impact

**✅ These warnings are completely harmless!**

Your pipeline **works perfectly** because:
1. ✅ The warnings are only DEBUG-level (not errors)
2. ✅ Force alignment falls back to a working method automatically
3. ✅ All 7 stages complete successfully
4. ✅ The pipeline completed in 20.8s with all outputs generated

**You can safely ignore these warnings.**

### Solutions

#### Option 1: Warnings Already Suppressed (Recommended - Default)

**✅ Fixed automatically!** The logging configuration now suppresses these DEBUG warnings by default. They won't appear in normal mode.

To see them again (for debugging), use `--verbose`:
```bash
heygen-clipper --verbose process ...
```

#### Option 2: Fix FFmpeg Library Linking (Optional - Advanced)

If you want to completely eliminate the warnings at the DEBUG level, you can create symbolic links:

```bash
# 1. Find your Homebrew FFmpeg installation
brew --prefix ffmpeg
# Should show: /opt/homebrew/opt/ffmpeg (Apple Silicon)
#          or: /usr/local/opt/ffmpeg (Intel Mac)

# 2. Activate your conda environment
conda activate brainbinge

# 3. Get conda lib directory
CONDA_LIB=$(conda info --base)/envs/brainbinge/lib

# 4. Create symbolic links (FFmpeg 8.0 uses libavutil.60)
ln -sf /opt/homebrew/opt/ffmpeg/lib/libavutil.60.dylib $CONDA_LIB/libavutil.58.dylib
ln -sf /opt/homebrew/opt/ffmpeg/lib/libavutil.60.dylib $CONDA_LIB/libavutil.57.dylib
ln -sf /opt/homebrew/opt/ffmpeg/lib/libavutil.60.dylib $CONDA_LIB/libavutil.56.dylib

# 5. Verify links
ls -la $CONDA_LIB/libavutil.*
```

**⚠️ Warning**: This creates version mismatches and may cause compatibility issues. **Only recommended for advanced users.**

#### Option 3: Use System PyTorch Audio (Not Recommended)

```bash
conda activate brainbinge

# Uninstall pip version
pip uninstall torchaudio

# Install conda version (may not match your PyTorch)
conda install -c pytorch torchaudio
```

**Note**: This may cause PyTorch version conflicts. Not recommended.

### Verification

After applying fixes, test the pipeline:

```bash
# Without verbose (should be clean)
heygen-clipper process --video data/test_samples/sample_01/video.mp4 \
    --script data/test_samples/sample_01/script.txt \
    --config config/brand_example.yaml \
    --output data/output

# With verbose (to see if warnings persist)
heygen-clipper --verbose process ... | grep "Failed to load"
```

---

## B-Roll Search Keywords

### How B-Roll Clips Are Searched

B-roll clips are fetched from the **Pexels API** using search keywords defined in your B-roll plan CSV file.

#### B-Roll Plan CSV Format

Location: `data/input/sample_broll_plan.csv`

```csv
start_sec,end_sec,type,search_query,fade_in,fade_out
3.0,6.5,fullframe,team collaboration,0.3,0.3
8.0,11.0,fullframe,office workspace,0.3,0.3
13.0,16.5,fullframe,business meeting,0.3,0.3
18.5,21.5,fullframe,technology innovation,0.3,0.3
24.0,27.0,fullframe,digital marketing,0.3,0.3
```

**Column Definitions:**

| Column | Description | Example |
|--------|-------------|---------|
| **start_sec** | When to start showing B-roll (seconds) | `3.0` |
| **end_sec** | When to stop showing B-roll (seconds) | `6.5` |
| **type** | Display mode: `fullframe` (recommended) or `pip` | `fullframe` |
| **search_query** | Pexels search keyword(s) | `team collaboration` |
| **fade_in** | Fade in duration (seconds) | `0.3` |
| **fade_out** | Fade out duration (seconds) | `0.3` |

#### How Keywords Are Used

1. **CSV Parsing**: The system reads your B-roll plan CSV
2. **Pexels Search**: For each row, it searches Pexels API using the `search_query` value
3. **Video Selection**: Finds best matching video (HD quality, landscape orientation, sufficient duration)
4. **Caching**: Downloads and caches videos (MD5 hash of query) to avoid repeated API calls
5. **Composition**: Overlays B-roll at specified times during video composition

#### Search Query Best Practices

**Good Keywords** (specific, actionable, visual):
- ✅ `team collaboration` - clear visual concept
- ✅ `office workspace` - specific environment
- ✅ `digital marketing` - recognizable activity
- ✅ `technology innovation` - broad but visual
- ✅ `business meeting` - common, easy to find

**Bad Keywords** (too abstract, text-based):
- ❌ `strategy` - too abstract
- ❌ `thinking` - not visually distinctive
- ❌ `concept` - too vague
- ❌ `idea` - hard to visualize
- ❌ `efficiency` - abstract noun

#### Keyword Selection Strategy

**Match Content to Visuals:**

| Video Topic | Good Keywords |
|-------------|---------------|
| Marketing video | `digital advertising`, `social media content`, `branding design` |
| Tech product | `software development`, `coding workspace`, `technology interface` |
| Business pitch | `business presentation`, `corporate meeting`, `team discussion` |
| Productivity | `focused workspace`, `organized desk`, `productivity tools` |
| Wellness | `meditation practice`, `healthy lifestyle`, `morning routine` |

**Tips:**
1. **Use 2-3 words** - More specific than single words, not overly complex
2. **Think visually** - What would this look like on camera?
3. **Test searches** - Visit [Pexels.com](https://www.pexels.com/videos/) and search your keywords first
4. **Check cache** - Reusing keywords = instant retrieval (no API calls)

#### Technical Constraints

- **Duration**: Each B-roll is automatically trimmed to **max 3.5 seconds**
- **Count**: Plan should include **minimum 5 B-roll clips**
- **Timing**: First B-roll should start after **3 seconds** (avatar intro), last should end before video finishes (avatar outro)
- **Type**: Use `fullframe` for TikTok-style full-screen overlays (recommended over `pip`)
- **Quality**: System automatically selects HD (1280×720) videos when available
- **Rate Limit**: Pexels free tier allows 200 API requests/hour (cached clips don't count)

#### API Key Setup

Set your Pexels API key to enable B-roll downloads:

```bash
# .env file
PEXELS_API_KEY=your_api_key_here
```

Get free API key: https://www.pexels.com/api/

#### Viewing Current Plan

To see what B-roll will be used:

```bash
cat data/input/sample_broll_plan.csv
```

#### Testing Specific Keywords

To test if a keyword yields good results:

```bash
# Search Pexels directly
open "https://www.pexels.com/search/videos/YOUR_KEYWORD"

# Or test with CLI (downloads to cache)
heygen-clipper process \
    --video data/test_samples/sample_01/video.mp4 \
    --script data/test_samples/sample_01/script.txt \
    --broll-plan data/input/sample_broll_plan.csv \
    --config config/brand_example.yaml \
    --output data/output
```

#### Cache Location

Downloaded B-roll videos are cached at: `data/temp/broll_cache/`

Each file is named using MD5 hash of the search query (ensures consistent naming).

Clear cache if needed:
```bash
rm -rf data/temp/broll_cache/*
```

---

## Caption Position Customization

### How to Adjust Caption Position

Captions use the **ASS (Advanced SubStation Alpha)** format, which provides fine-grained control over positioning.

#### Quick Adjustments

To change the vertical position of captions, modify the **MarginV** parameter in `src/modules/styling.py`:

```python
# Line 343 in src/modules/styling.py
margin_v = 100  # Default: 100 (raised position for TikTok-style)

# Common values:
# margin_v = 20   # Low position (near bottom edge)
# margin_v = 50   # Medium-low position
# margin_v = 100  # Medium position (current default)
# margin_v = 150  # Medium-high position
# margin_v = 200  # High position (near middle of screen)
```

**Higher values = captions move UP from the bottom.**

#### Horizontal Width Adjustment

To make captions span MORE horizontal space across the screen:

```python
# Line 438-439 in src/modules/styling.py
margin_l = 30  # Left margin (distance from left edge)
margin_r = 30  # Right margin (distance from right edge)

# For WIDER captions (more horizontal space):
# margin_l = 20, margin_r = 20  # More width (1240px usable)
# margin_l = 15, margin_r = 15  # Even wider (1250px usable)
# margin_l = 10, margin_r = 10  # Maximum width (1260px usable)

# For NARROWER captions (more breathing room):
# margin_l = 40, margin_r = 40  # Less width (1200px usable)
# margin_l = 50, margin_r = 50  # Much narrower (1180px usable)
```

**Smaller margin values = wider caption text area**
**Larger margin values = narrower caption text area (more padding)**

On a 1280px wide screen:
- Usable width = 1280 - margin_l - margin_r
- Current (30, 30) = 1220px wide
- Maximum (10, 10) = 1260px wide

#### ASS Format Parameters

The ASS style definition controls all caption styling:

```
Style: Default,{font},{size},{colors},...,Alignment,MarginL,MarginR,MarginV,Encoding
                                        ↑         ↑       ↑       ↑
                                        Position  Left    Right   Vertical
```

**Key Parameters**:

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| **MarginV** | Vertical margin from bottom (pixels) | 100 | 0-500 |
| **MarginL** | Left margin (pixels) | 30 | 0-200 |
| **MarginR** | Right margin (pixels) | 30 | 0-200 |
| **Alignment** | Position on 9-grid (numpad layout) | 2 | 1-9 |

**Alignment Grid** (like numpad):
```
7 = Top-Left      8 = Top-Center      9 = Top-Right
4 = Middle-Left   5 = Center          6 = Middle-Right
1 = Bottom-Left   2 = Bottom-Center   3 = Bottom-Right
```

Current default: `Alignment=2` (bottom-center)

#### Font Size Customization

To change font size (currently 2x default = 56pt):

```python
# Line 83 in src/modules/styling.py
self.font_size = 56  # TikTok-style extra large font (current default)

# Common values:
# 28pt = Standard size (readable but subtle)
# 42pt = Large size (1.5x)
# 48pt = Extra large (1.7x)
# 56pt = Maximum size (2x, current default)
# 64pt = Extreme size (very dominant)
```

#### Background Box Customization

Captions now have a **semi-transparent black background box** for better readability:

```python
# Lines 442-443 in src/modules/styling.py
back_color = "&H80000000"  # 50% transparent black
border_style = 3           # 3 = Opaque box

# Transparency levels (ASS alpha: 00=opaque, FF=transparent):
# &H00000000 = Fully opaque black (0% transparency)
# &H40000000 = 25% transparent black
# &H80000000 = 50% transparent black (current default)
# &HC0000000 = 75% transparent black (very subtle)
# &HFF000000 = Fully transparent (no box)

# Border styles:
# border_style = 1  # Outline only (no background box)
# border_style = 3  # Opaque background box (current default)
```

**⚠️ Rounded Corners Limitation**: ASS subtitle format does not support rounded corners natively. The background box will have **square corners**. For rounded corners, you would need to use a different subtitle format or custom overlay approach (not currently supported).

To disable the background box entirely:
```python
back_color = "&HFF000000"  # Fully transparent
# or
border_style = 1  # Outline only
```

#### Word Highlighting Colors

To customize the highlight color for TikTok-style word-by-word effects:

```python
# Line 106 in src/modules/styling.py
self.highlight_color = "#FFD700"  # Gold (default)

# Alternative colors:
# "#FFD700" = Gold (TikTok-style)
# "#FF69B4" = Hot Pink (playful)
# "#00FF00" = Lime Green (energetic)
# "#FF4500" = Orange Red (bold)
# "#1E90FF" = Dodger Blue (cool)
```

#### Configuration File Method (Recommended)

For production use, customize via `config/brand_example.yaml`:

```yaml
captions:
  font:
    family: "Arial"
    size: 42        # Font size in points
    weight: "bold"

  style:
    color: "#FFFFFF"           # Text color (white)
    stroke_color: "#000000"    # Outline color (black)
    stroke_width: 3            # Outline width in pixels
    word_highlight: true       # Enable TikTok-style highlighting
    highlight_color: "#FFD700" # Highlight color (gold)

    # Position settings (requires code modification)
    # margin_v: 100            # Vertical margin (not yet configurable)
    # alignment: 2             # Bottom-center (not yet configurable)
```

**Note**: MarginV and Alignment are currently hard-coded but can be made configurable if needed.

#### Testing Your Changes

After modifying position settings:

1. **Re-run Stage 4 only** (if you have existing outputs):
   ```bash
   # Quick test with existing alignment
   python -c "from src.modules.styling import CaptionStyler; from src.config import Config; \
              from pathlib import Path; \
              cfg = Config.from_yaml('config/brand_example.yaml'); \
              styler = CaptionStyler(cfg); \
              styler.process(Path('data/output/captions/video.srt'), \
                            Path('data/output/styled/video_test.ass'), \
                            alignment_json=Path('data/output/alignment/video.json'))"
   ```

2. **Or re-run full pipeline**:
   ```bash
   heygen-clipper process \
       --video data/test_samples/sample_01/video.mp4 \
       --script data/test_samples/sample_01/script.txt \
       --config config/brand_example.yaml \
       --output data/output
   ```

3. **Preview the video**:
   ```bash
   ffplay data/output/final/video_final.mp4
   ```

#### Advanced: Custom ASS Styles

For full control, you can manually edit the generated `.ass` file in `data/output/styled/`:

```ass
[V4+ Styles]
Style: Default,Arial,42,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,0,2,10,10,100,1
                                                                                            ↑  ↑  ↑  ↑
                                                                                         Align L  R  V
```

Edit the last 4 values (Alignment, MarginL, MarginR, MarginV) to customize positioning.

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
