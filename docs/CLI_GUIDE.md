# CLI Guide - HeyGen Social Clipper

Complete guide to using the `heygen-clipper` command-line interface.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Commands](#commands)
  - [process](#process-command)
  - [validate](#validate-command)
  - [batch](#batch-command)
  - [config](#config-commands)
- [Options](#global-options)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

## Installation

Install the package in development mode:

```bash
pip install -e .
```

Or install from PyPI (when published):

```bash
pip install heygen-social-clipper
```

Verify installation:

```bash
heygen-clipper --version
```

## Quick Start

### 1. Set up environment

Create a `.env` file with your API keys:

```bash
# Required for B-roll fetching
PEXELS_API_KEY=your_pexels_api_key_here
```

### 2. Prepare your files

- **Video**: HeyGen output video (`.mp4`)
- **Script**: Word-perfect script (`.txt`)
- **Config**: Brand configuration (`.yaml` or `.json`)
- **B-roll Plan**: (Optional) CSV with B-roll timing and queries

### 3. Process your video

```bash
heygen-clipper process \
    --video data/input/video.mp4 \
    --script data/input/script.txt \
    --config config/brand.yaml \
    --output data/output
```

### 4. Check your output

The final video will be at: `data/output/final/video_final.mp4`

---

## Commands

### `process` Command

Process a single HeyGen video through the complete 7-stage pipeline.

#### Syntax

```bash
heygen-clipper process [OPTIONS]
```

#### Required Options

| Option | Type | Description |
|--------|------|-------------|
| `--video` | PATH | Path to HeyGen input video (MP4) |
| `--script` | PATH | Path to word-perfect script (TXT) |
| `--config` | PATH | Path to brand configuration (YAML/JSON) |
| `--output` | PATH | Output directory for processed videos |

#### Optional Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--platform` | CHOICE | `all` | Target platform: `instagram`, `tiktok`, `youtube`, or `all` |
| `--broll-plan` | PATH | - | Path to B-roll plan CSV (optional) |

#### Example

```bash
heygen-clipper process \
    --video heygen_output.mp4 \
    --script script.txt \
    --config config/mybrand.yaml \
    --output output/ \
    --platform instagram
```

#### Pipeline Stages

The `process` command executes 7 stages:

1. **Audio Extraction** - Extract audio from video (16kHz mono)
2. **Force Alignment** - Word-level timestamps using Whisper
3. **Caption Generation** - Create SRT captions with word timing
4. **Caption Styling** - Apply brand styling (ASS subtitles)
5. **B-roll Integration** - Fetch and cache B-roll clips from Pexels
6. **Video Composition** - Combine video, captions, and B-roll
7. **Video Encoding** - Hardware-accelerated H.265 encoding

#### Output Structure

```
output/
├── audio/
│   └── video.wav              # Extracted audio
├── alignment/
│   └── video.json             # Word-level timestamps
├── captions/
│   └── video.srt              # SRT captions
├── styled/
│   └── video.ass              # Styled ASS captions
├── broll/
│   └── video_clips.json       # B-roll metadata
├── composed/
│   └── video.mp4              # Composed video (before encoding)
└── final/
    └── video_final.mp4        # ✨ Final encoded video
```

---

### `validate` Command

Validate configuration and input files without processing.

#### Syntax

```bash
heygen-clipper validate [OPTIONS]
```

#### Options

All options are optional - specify what you want to validate:

| Option | Type | Description |
|--------|------|-------------|
| `--video` | PATH | Validate video file |
| `--script` | PATH | Validate script file |
| `--config` | PATH | Validate configuration file |
| `--broll-plan` | PATH | Validate B-roll plan CSV |

#### Example

```bash
# Validate all inputs
heygen-clipper validate \
    --video video.mp4 \
    --script script.txt \
    --config config.yaml \
    --broll-plan broll_plan.csv

# Validate only config
heygen-clipper validate --config config.yaml
```

#### Validation Checks

- ✅ File existence
- ✅ File format (extensions)
- ✅ File size (not empty)
- ✅ Configuration schema
- ✅ Environment variables (PEXELS_API_KEY)

---

### `batch` Command

Process multiple videos in batch mode.

#### Syntax

```bash
heygen-clipper batch [OPTIONS]
```

#### Options

| Option | Type | Description |
|--------|------|-------------|
| `--input-dir` | PATH | Directory containing videos and scripts |
| `--config` | PATH | Brand configuration file |
| `--output-dir` | PATH | Output directory |
| `--workers` | INT | Number of parallel workers (default: 1) |

#### Example

```bash
heygen-clipper batch \
    --input-dir data/batch_input/ \
    --config config/brand.yaml \
    --output-dir data/batch_output/ \
    --workers 4
```

#### Input Directory Structure

```
batch_input/
├── video1.mp4
├── video1.txt
├── video2.mp4
├── video2.txt
└── ...
```

Videos and scripts are matched by filename (same basename).

---

### `config` Commands

Manage configuration files.

#### `config init` - Generate Template

Create a default configuration file:

```bash
heygen-clipper config init --output mybrand.yaml
```

Options:
- `--output`: Output path (default: `config/brand.yaml`)
- `--format`: Format - `yaml` or `json` (default: `yaml`)

#### `config show` - Display Configuration

Display current configuration:

```bash
heygen-clipper config show --config mybrand.yaml
```

---

## Global Options

These options apply to all commands:

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Enable verbose (DEBUG) logging |
| `-q, --quiet` | Suppress output (errors only) |
| `--log-file PATH` | Log to file in addition to console |
| `--version` | Show version and exit |
| `--help` | Show help message and exit |

### Example with Global Options

```bash
heygen-clipper --verbose --log-file debug.log process \
    --video video.mp4 \
    --script script.txt \
    --config config.yaml \
    --output output/
```

---

## Examples

### Example 1: Basic Processing

```bash
heygen-clipper process \
    --video data/input/heygen_video.mp4 \
    --script data/input/script.txt \
    --config config/brand_example.yaml \
    --output data/output
```

### Example 2: Instagram-Specific Output

```bash
heygen-clipper process \
    --video video.mp4 \
    --script script.txt \
    --config config/instagram.yaml \
    --output output/ \
    --platform instagram
```

### Example 3: Debugging with Verbose Logging

```bash
heygen-clipper --verbose --log-file debug.log process \
    --video video.mp4 \
    --script script.txt \
    --config config.yaml \
    --output output/
```

### Example 4: Validate Before Processing

```bash
# First validate
heygen-clipper validate \
    --video video.mp4 \
    --script script.txt \
    --config config.yaml

# Then process
heygen-clipper process \
    --video video.mp4 \
    --script script.txt \
    --config config.yaml \
    --output output/
```

### Example 5: Batch Processing

```bash
heygen-clipper batch \
    --input-dir data/videos/ \
    --config config/brand.yaml \
    --output-dir data/processed/ \
    --workers 4
```

---

## Troubleshooting

### Common Issues

#### 1. "PEXELS_API_KEY not found"

**Problem**: B-roll fetching requires Pexels API key.

**Solution**:
```bash
# Add to .env file
echo "PEXELS_API_KEY=your_key_here" >> .env

# Or set environment variable
export PEXELS_API_KEY=your_key_here
```

#### 2. "Video file not found"

**Problem**: File path is incorrect or file doesn't exist.

**Solution**:
- Use absolute paths: `/Users/you/videos/video.mp4`
- Or relative from current directory: `data/input/video.mp4`
- Verify with: `ls -la data/input/video.mp4`

#### 3. "FFmpeg not found"

**Problem**: FFmpeg not installed or not in PATH.

**Solution**:
```bash
# macOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt-get install ffmpeg

# Verify installation
ffmpeg -version
```

#### 4. "Pipeline failed at Stage X"

**Problem**: One stage failed during processing.

**Solution**:
1. Run with `--verbose` to see detailed logs
2. Check intermediate outputs in `output/` directory
3. Verify input files are valid
4. Check available disk space

#### 5. "VideoToolbox encoding failed"

**Problem**: Hardware acceleration not available.

**Solution**: The system automatically falls back to software encoding (libx264). This is normal on non-Mac systems or older Macs.

### Getting Help

Run any command with `--help`:

```bash
heygen-clipper --help
heygen-clipper process --help
heygen-clipper validate --help
```

---

## Advanced Usage

### Custom Configuration

Create custom brand configuration:

```yaml
# config/mybrand.yaml
brand:
  name: "My Brand"
  colors:
    primary: "#FF6B6B"
    secondary: "#4ECDC4"
  fonts:
    primary: "Arial"

captions:
  font_size: 32
  position: "bottom"
  max_words_per_caption: 3

video:
  resolution: "1280x720"
  fps: 30
  bitrate: "5000k"

encoding:
  codec: "hevc_videotoolbox"
  fallback_codec: "libx264"
  target_size_mb: 30
```

### Environment Variables

All configuration values can be overridden via environment variables:

```bash
export PEXELS_API_KEY=your_key
export LOG_LEVEL=DEBUG
export WEBHOOK_SECRET=your_secret

heygen-clipper process ...
```

### Progress Tracking

Monitor stage completion with timing information:

```bash
heygen-clipper --verbose process ...
```

Output:
```
08:00:00 [INFO] Stage 1/7: Audio Extraction
08:00:05 [INFO] Completed: Stage 1 (4.3s)
08:00:05 [INFO] Stage 2/7: Force Alignment
08:01:20 [INFO] Completed: Stage 2 (75.2s)
...
```

### Performance Optimization

#### Hardware Acceleration

On Mac M2/M3:
- VideoToolbox automatically enabled
- 2-3× faster encoding
- Lower CPU usage

#### Parallel Processing

For batch operations:
```bash
heygen-clipper batch --workers 4 ...
```

Use workers = number of CPU cores for best performance.

---

## Configuration Reference

See [Configuration Guide](./CONFIGURATION.md) for detailed configuration options.

## API Reference

See [API Documentation](./API.md) for programmatic usage.

## Support

- **Issues**: https://github.com/colehanan1/BrainBinge-Video-Editor/issues
- **Discussions**: https://github.com/colehanan1/BrainBinge-Video-Editor/discussions
- **Email**: support@brainbinge.com

---

**Last Updated**: 2025-01-13
**Version**: 0.1.0-alpha
