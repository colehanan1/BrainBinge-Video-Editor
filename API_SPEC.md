# API Specification - HeyGen Social Clipper

> Complete reference for CLI commands, configuration formats, and integration interfaces

## Table of Contents

- [CLI Commands](#cli-commands)
- [Configuration File Formats](#configuration-file-formats)
- [Script File Format](#script-file-format)
- [Webhook Integration](#webhook-integration)
- [Output Formats](#output-formats)
- [Error Codes](#error-codes)

## CLI Commands

### Global Options

All commands support the following global options:

```bash
--verbose, -v          Enable verbose logging
--quiet, -q            Suppress non-error output
--log-file PATH        Write logs to specified file
--config-dir PATH      Custom configuration directory
--version              Show version and exit
--help, -h             Show help message and exit
```

---

### `heygen-clipper process`

Process a single HeyGen video into social media content.

#### Syntax

```bash
heygen-clipper process [OPTIONS]
```

#### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `--video PATH` | File | Yes | - | Path to HeyGen video file (MP4) |
| `--script PATH` | File | Yes | - | Path to script file (JSON/SRT) |
| `--config PATH` | File | Yes | - | Path to brand configuration (YAML/JSON) |
| `--output DIR` | Directory | Yes | - | Output directory for processed videos |
| `--platform` | Choice | No | all | Target platform: `instagram`, `tiktok`, `youtube`, `all` |
| `--quality` | Choice | No | high | Output quality: `low`, `medium`, `high`, `ultra` |
| `--no-captions` | Flag | No | False | Disable caption generation |
| `--no-broll` | Flag | No | False | Disable B-roll integration |
| `--no-music` | Flag | No | False | Disable background music |
| `--preview` | Flag | No | False | Generate low-quality preview only |
| `--overwrite` | Flag | No | False | Overwrite existing output files |

#### Examples

```bash
# Basic processing
heygen-clipper process \
  --video input/video.mp4 \
  --script input/script.json \
  --config config/brand.yaml \
  --output output/

# Instagram only, no B-roll
heygen-clipper process \
  --video input/video.mp4 \
  --script input/script.json \
  --config config/brand.yaml \
  --output output/ \
  --platform instagram \
  --no-broll

# Preview mode for testing
heygen-clipper process \
  --video input/video.mp4 \
  --script input/script.json \
  --config config/brand.yaml \
  --output output/ \
  --preview
```

#### Exit Codes

- `0` - Success
- `1` - General error
- `2` - Invalid input file
- `3` - Configuration error
- `4` - Processing failure

---

### `heygen-clipper batch`

Process multiple videos in batch mode.

#### Syntax

```bash
heygen-clipper batch [OPTIONS]
```

#### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `--input-dir DIR` | Directory | Yes | - | Directory containing videos and scripts |
| `--config PATH` | File | Yes | - | Path to brand configuration |
| `--output-dir DIR` | Yes | - | Output directory for all processed videos |
| `--pattern GLOB` | String | No | `*.mp4` | File pattern to match videos |
| `--workers INT` | Integer | No | 1 | Number of parallel workers |
| `--continue-on-error` | Flag | No | False | Continue processing if one video fails |
| `--max-videos INT` | Integer | No | - | Limit number of videos to process |

#### Expected Directory Structure

```
input-dir/
├── video1.mp4
├── video1.json          # or video1.srt
├── video2.mp4
├── video2.json
└── ...
```

The script file must have the same basename as the video file.

#### Examples

```bash
# Process all videos in directory
heygen-clipper batch \
  --input-dir videos/ \
  --config config/brand.yaml \
  --output-dir output/

# Parallel processing with error tolerance
heygen-clipper batch \
  --input-dir videos/ \
  --config config/brand.yaml \
  --output-dir output/ \
  --workers 4 \
  --continue-on-error
```

---

### `heygen-clipper watch`

Watch a directory and auto-process new videos.

#### Syntax

```bash
heygen-clipper watch [OPTIONS]
```

#### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `--watch-dir DIR` | Directory | Yes | - | Directory to monitor for new files |
| `--config PATH` | File | Yes | - | Path to brand configuration |
| `--output-dir DIR` | Directory | Yes | - | Output directory |
| `--poll-interval INT` | Integer | No | 5 | Polling interval in seconds |
| `--process-existing` | Flag | No | False | Process existing files on startup |

#### Examples

```bash
# Watch directory for new videos
heygen-clipper watch \
  --watch-dir /path/to/incoming \
  --config config/brand.yaml \
  --output-dir /path/to/processed

# Process existing files and continue watching
heygen-clipper watch \
  --watch-dir /path/to/incoming \
  --config config/brand.yaml \
  --output-dir /path/to/processed \
  --process-existing
```

---

### `heygen-clipper webhook`

Start webhook server for Make.com integration.

#### Syntax

```bash
heygen-clipper webhook [OPTIONS]
```

#### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `--host STRING` | String | No | `0.0.0.0` | Server host address |
| `--port INT` | Integer | No | 8000 | Server port |
| `--secret STRING` | String | No | - | Webhook secret for authentication |
| `--config PATH` | File | Yes | - | Path to brand configuration |
| `--output-dir DIR` | Directory | Yes | - | Output directory |
| `--max-workers INT` | Integer | No | 2 | Max concurrent processing jobs |

#### Examples

```bash
# Start webhook server
heygen-clipper webhook \
  --port 8000 \
  --secret my-secret-key \
  --config config/brand.yaml \
  --output-dir /path/to/output

# Production server with multiple workers
heygen-clipper webhook \
  --host 0.0.0.0 \
  --port 80 \
  --secret $WEBHOOK_SECRET \
  --config config/brand.yaml \
  --output-dir /var/heygen-output \
  --max-workers 4
```

---

### `heygen-clipper validate`

Validate configuration and input files without processing.

#### Syntax

```bash
heygen-clipper validate [OPTIONS]
```

#### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `--config PATH` | File | No | - | Validate brand configuration |
| `--script PATH` | File | No | - | Validate script file |
| `--video PATH` | File | No | - | Validate video file |
| `--all` | Flag | No | False | Validate all provided files |

#### Examples

```bash
# Validate configuration
heygen-clipper validate --config config/brand.yaml

# Validate all inputs
heygen-clipper validate \
  --config config/brand.yaml \
  --script input/script.json \
  --video input/video.mp4 \
  --all
```

---

### `heygen-clipper config`

Manage and generate configuration files.

#### Syntax

```bash
heygen-clipper config [SUBCOMMAND]
```

#### Subcommands

**`init`** - Generate template configuration file

```bash
heygen-clipper config init \
  --output config/brand.yaml \
  --format yaml  # or json
```

**`show`** - Display current configuration

```bash
heygen-clipper config show --config config/brand.yaml
```

**`validate`** - Validate configuration file

```bash
heygen-clipper config validate --config config/brand.yaml
```

---

## Configuration File Formats

### Brand Configuration (YAML)

```yaml
# Brand Configuration for HeyGen Social Clipper
version: "1.0"

brand:
  name: "BrainBinge"
  logo: "assets/logo.png"
  watermark: "assets/watermark.png"

  # Color scheme (hex codes)
  colors:
    primary: "#FF6B35"
    secondary: "#004E89"
    accent: "#F7B801"
    text: "#FFFFFF"
    background: "#000000"

captions:
  enabled: true

  # Font configuration
  font:
    family: "Montserrat"
    weight: "bold"
    size: 48

  # Caption styling
  style:
    color: "#FFFFFF"
    background_color: "#000000"
    background_opacity: 0.7
    stroke_color: "#000000"
    stroke_width: 2

  # Positioning
  position:
    vertical: "bottom"  # top, center, bottom
    horizontal: "center"  # left, center, right
    margin_bottom: 150  # pixels from bottom

  # Animation
  animation:
    type: "word_highlight"  # none, word_highlight, fade_in, slide_in
    duration: 0.2  # seconds
    highlight_color: "#F7B801"

broll:
  enabled: true

  # B-roll sources
  sources:
    - type: "pexels"
      api_key: "${PEXELS_API_KEY}"
      enabled: true
    - type: "local"
      path: "assets/broll"
      enabled: true

  # B-roll behavior
  settings:
    min_duration: 2.0  # seconds
    max_duration: 5.0  # seconds
    transition_type: "crossfade"  # cut, crossfade, fade
    transition_duration: 0.5  # seconds
    opacity: 1.0  # 0.0 to 1.0

  # Keyword mapping for smart B-roll selection
  keywords:
    "technology": ["computer", "coding", "tech"]
    "nature": ["forest", "ocean", "mountain"]
    "business": ["office", "meeting", "handshake"]
    "science": ["laboratory", "microscope", "experiment"]

audio:
  # Background music
  music:
    enabled: true
    source: "assets/music"  # directory with music files
    volume: 0.15  # 0.0 to 1.0
    fade_in: 1.0  # seconds
    fade_out: 1.0  # seconds

  # Audio processing
  processing:
    normalize: true
    compression: true
    voice_volume: 1.0
    noise_reduction: false

overlays:
  # Logo overlay
  logo:
    enabled: true
    path: "assets/logo.png"
    position: "top_right"  # top_left, top_right, bottom_left, bottom_right
    size: 100  # pixels (width)
    margin: 20  # pixels from edge
    opacity: 0.8

  # Watermark
  watermark:
    enabled: true
    path: "assets/watermark.png"
    position: "bottom_right"
    size: 80
    margin: 20
    opacity: 0.5

export:
  # Platform-specific settings
  platforms:
    instagram:
      enabled: true
      resolution: [1080, 1920]
      fps: 30
      bitrate: "10M"
      codec: "h264"
      profile: "high"

    tiktok:
      enabled: true
      resolution: [1080, 1920]
      fps: 30
      bitrate: "8M"
      codec: "h264"
      profile: "high"

    youtube:
      enabled: true
      resolution: [1080, 1920]
      fps: 30
      bitrate: "12M"
      codec: "h264"
      profile: "high"

  # Output naming
  naming:
    template: "{brand}_{timestamp}_{platform}"
    # Available variables: {brand}, {timestamp}, {platform}, {date}

  # Metadata generation
  metadata:
    generate: true
    include_hashtags: true
    include_description: true
```

### Brand Configuration (JSON)

```json
{
  "version": "1.0",
  "brand": {
    "name": "BrainBinge",
    "logo": "assets/logo.png",
    "watermark": "assets/watermark.png",
    "colors": {
      "primary": "#FF6B35",
      "secondary": "#004E89",
      "accent": "#F7B801",
      "text": "#FFFFFF",
      "background": "#000000"
    }
  },
  "captions": {
    "enabled": true,
    "font": {
      "family": "Montserrat",
      "weight": "bold",
      "size": 48
    },
    "style": {
      "color": "#FFFFFF",
      "background_color": "#000000",
      "background_opacity": 0.7
    }
  }
}
```

---

## Script File Format

### JSON Format (Recommended)

```json
{
  "version": "1.0",
  "metadata": {
    "title": "Understanding Neural Networks",
    "duration": 60.5,
    "language": "en",
    "created": "2025-11-12T10:00:00Z"
  },
  "segments": [
    {
      "id": 1,
      "start": 0.0,
      "end": 3.5,
      "text": "Welcome to BrainBinge, where we make learning addictive!",
      "speaker": "narrator",
      "emphasis": ["BrainBinge"],
      "broll_keywords": ["welcome", "learning"]
    },
    {
      "id": 2,
      "start": 3.5,
      "end": 8.2,
      "text": "Today we're diving into neural networks and how they work.",
      "speaker": "narrator",
      "emphasis": ["neural networks"],
      "broll_keywords": ["neural networks", "brain", "technology"]
    },
    {
      "id": 3,
      "start": 8.2,
      "end": 14.0,
      "text": "Neural networks are inspired by the human brain's structure.",
      "speaker": "narrator",
      "broll_keywords": ["brain", "neurons", "science"]
    }
  ],
  "markers": [
    {
      "time": 0.0,
      "type": "intro",
      "note": "Show logo animation"
    },
    {
      "time": 30.0,
      "type": "transition",
      "note": "B-roll heavy section"
    }
  ]
}
```

### SRT Format (Alternative)

```srt
1
00:00:00,000 --> 00:00:03,500
Welcome to BrainBinge, where we make learning addictive!

2
00:00:03,500 --> 00:00:08,200
Today we're diving into neural networks and how they work.

3
00:00:08,200 --> 00:00:14,000
Neural networks are inspired by the human brain's structure.
```

**Note:** SRT format is supported but JSON is preferred as it provides:
- Emphasis markers
- B-roll keyword hints
- Speaker identification
- Additional metadata

---

## Webhook Integration

### Endpoint

```
POST /webhook/process
```

### Authentication

Include the webhook secret in the `X-Webhook-Secret` header:

```
X-Webhook-Secret: your-secret-key
```

### Request Payload

```json
{
  "video_url": "https://storage.example.com/videos/video123.mp4",
  "script_url": "https://storage.example.com/scripts/script123.json",
  "config_override": {
    "platforms": ["instagram", "tiktok"]
  },
  "callback_url": "https://api.example.com/webhook/complete",
  "metadata": {
    "user_id": "user123",
    "project_id": "proj456",
    "custom_field": "value"
  }
}
```

### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `video_url` | String (URL) | Yes | URL to download HeyGen video |
| `script_url` | String (URL) | Yes | URL to download script file |
| `config_override` | Object | No | Override default config settings |
| `callback_url` | String (URL) | No | URL to POST completion notification |
| `metadata` | Object | No | Custom metadata to include in response |

### Response (Immediate)

```json
{
  "status": "queued",
  "job_id": "job_abc123",
  "message": "Video processing queued",
  "estimated_duration": 180
}
```

### Callback Payload (On Completion)

```json
{
  "job_id": "job_abc123",
  "status": "completed",
  "outputs": [
    {
      "platform": "instagram",
      "video_path": "/output/BrainBinge_20251112_instagram.mp4",
      "captions_path": "/output/BrainBinge_20251112_instagram.srt",
      "metadata_path": "/output/BrainBinge_20251112_instagram_metadata.json",
      "thumbnail_path": "/output/BrainBinge_20251112_instagram_thumb.jpg"
    },
    {
      "platform": "tiktok",
      "video_path": "/output/BrainBinge_20251112_tiktok.mp4",
      "captions_path": "/output/BrainBinge_20251112_tiktok.srt",
      "metadata_path": "/output/BrainBinge_20251112_tiktok_metadata.json",
      "thumbnail_path": "/output/BrainBinge_20251112_tiktok_thumb.jpg"
    }
  ],
  "processing_time": 147.5,
  "metadata": {
    "user_id": "user123",
    "project_id": "proj456"
  }
}
```

### Error Response

```json
{
  "status": "error",
  "job_id": "job_abc123",
  "error_code": "INVALID_VIDEO",
  "error_message": "Video file is corrupted or invalid format",
  "details": {
    "file": "video123.mp4",
    "reason": "Unable to decode video stream"
  }
}
```

---

## Output Formats

### Video Output

Each platform generates:
- `{name}_{platform}.mp4` - Final video file
- `{name}_{platform}.srt` - Caption file (SRT format)
- `{name}_{platform}_metadata.json` - Metadata file
- `{name}_{platform}_thumb.jpg` - Thumbnail image

### Metadata File

```json
{
  "platform": "instagram",
  "video_info": {
    "duration": 58.5,
    "resolution": [1080, 1920],
    "fps": 30,
    "codec": "h264",
    "bitrate": "10M",
    "file_size_mb": 12.3
  },
  "suggested_caption": "🧠 Ever wondered how neural networks work? Let's break it down! 🤖✨",
  "hashtags": [
    "#BrainBinge",
    "#NeuralNetworks",
    "#AI",
    "#MachineLearning",
    "#Education",
    "#LearnOnTikTok",
    "#TechEducation",
    "#Science"
  ],
  "segments_count": 15,
  "broll_scenes": 8,
  "processing_info": {
    "processed_at": "2025-11-12T15:30:00Z",
    "processing_time_seconds": 147.5,
    "pipeline_version": "1.0.0"
  }
}
```

---

## Error Codes

| Code | Name | Description | Resolution |
|------|------|-------------|------------|
| `E001` | `INVALID_VIDEO` | Video file is invalid or corrupted | Check video file integrity |
| `E002` | `INVALID_SCRIPT` | Script file format is invalid | Validate JSON/SRT format |
| `E003` | `INVALID_CONFIG` | Configuration file has errors | Run `validate` command |
| `E004` | `MISSING_FILE` | Required file not found | Check file paths |
| `E005` | `UNSUPPORTED_FORMAT` | File format not supported | Convert to supported format |
| `E006` | `RESOLUTION_ERROR` | Video resolution incompatible | Use 1080x1920 or 1920x1080 |
| `E007` | `PROCESSING_FAILED` | Video processing failed | Check logs for details |
| `E008` | `API_ERROR` | External API call failed | Check API keys and connectivity |
| `E009` | `INSUFFICIENT_RESOURCES` | Not enough disk/memory | Free up resources |
| `E010` | `TIMEOUT` | Processing timeout exceeded | Reduce video length or quality |

---

## Environment Variables

```bash
# API Keys
PEXELS_API_KEY=your_pexels_api_key
WHISPER_API_KEY=your_whisper_api_key  # Optional

# Webhook Configuration
WEBHOOK_SECRET=your_webhook_secret
WEBHOOK_PORT=8000

# Processing Configuration
MAX_WORKERS=4
PROCESSING_TIMEOUT=600  # seconds
TEMP_DIR=/tmp/heygen-clipper

# Output Configuration
OUTPUT_DIR=/var/heygen-output
KEEP_TEMP_FILES=false

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FILE=/var/log/heygen-clipper.log
```

---

## Version History

- **v1.0** - Initial API specification
  - Core CLI commands
  - Configuration format v1.0
  - Script format v1.0
  - Webhook integration

---

**Last Updated:** 2025-11-12
