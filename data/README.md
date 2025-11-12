# Data Directory Guide

This directory contains sample inputs, test data, and processing outputs for the HeyGen Social Clipper project.

## Directory Structure

```
data/
├── README.md               # This file
├── input/                  # Sample input files
│   ├── sample_video.mp4   # Sample HeyGen video (to be added)
│   ├── sample_script.txt  # Sample script file (to be added)
│   └── sample_config.yaml # Sample configuration (to be added)
├── output/                 # Processed video outputs (auto-created)
└── temp/                   # Temporary processing files (auto-created)
```

## Input File Formats

### 1. Video Files (`input/`)

**Format:** MP4 (H.264 codec recommended)

**Specifications:**
- **Resolution:** 1080x1920 (9:16 vertical) or 1920x1080
- **Frame Rate:** 24fps, 30fps, or 60fps
- **Duration:** 30-90 seconds (optimized for social media)
- **Audio:** AAC or MP3, stereo or mono
- **Bitrate:** 5-20 Mbps

**Example:**
```
input/neural_networks_60s.mp4
input/quantum_physics_90s.mp4
```

### 2. Script Files (`input/`)

Scripts can be provided in multiple formats:

#### Format 1: Plain Text (`.txt`)
```
Welcome to BrainBinge! Today we're exploring neural networks.

Neural networks are inspired by the human brain's structure.

They consist of interconnected nodes called neurons.
```

**Note:** Plain text will be aligned with audio using force alignment to generate timestamps automatically.

#### Format 2: JSON with Timestamps (`.json`)
```json
{
  "version": "1.0",
  "metadata": {
    "title": "Understanding Neural Networks",
    "duration": 60.5,
    "language": "en"
  },
  "segments": [
    {
      "id": 1,
      "start": 0.0,
      "end": 3.5,
      "text": "Welcome to BrainBinge!",
      "emphasis": ["BrainBinge"],
      "broll_keywords": ["welcome", "greeting"]
    },
    {
      "id": 2,
      "start": 3.5,
      "end": 8.2,
      "text": "Today we're exploring neural networks.",
      "emphasis": ["neural networks"],
      "broll_keywords": ["neural networks", "brain", "technology"]
    }
  ]
}
```

#### Format 3: CSV (`.csv`)
```csv
start,end,text,broll_keywords
0.0,3.5,"Welcome to BrainBinge!","welcome,greeting"
3.5,8.2,"Today we're exploring neural networks.","neural networks,brain"
```

### 3. Configuration Files (`input/` or `config/`)

**Format:** YAML (`.yaml`) or JSON (`.json`)

**Example:** `sample_config.yaml`
```yaml
version: "1.0"
brand:
  name: "BrainBinge"
  logo: "assets/logo.png"
  colors:
    primary: "#FF6B35"

captions:
  enabled: true
  font:
    family: "Montserrat"
    size: 48
    weight: "bold"
  style:
    color: "#FFFFFF"
    background_color: "#000000"

export:
  platforms:
    instagram:
      enabled: true
      resolution: [1080, 1920]
      fps: 30
```

**Validation:** Use `heygen-clipper validate --config config.yaml` to validate configuration against schema.

## Output File Formats

### Processed Videos (`output/`)

**Naming Convention:** `{brand}_{timestamp}_{platform}.mp4`

**Example:**
```
output/BrainBinge_20251112_143022_instagram.mp4
output/BrainBinge_20251112_143022_tiktok.mp4
output/BrainBinge_20251112_143022_youtube.mp4
```

### Captions (`output/`)

**Formats:** SRT, VTT, ASS

**Example:**
```
output/BrainBinge_20251112_143022_instagram.srt
output/BrainBinge_20251112_143022_instagram_styled.ass
```

### Metadata (`output/`)

**Format:** JSON

**Example:** `BrainBinge_20251112_143022_instagram_metadata.json`
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
  "suggested_caption": "🧠 Ever wondered how neural networks work?",
  "hashtags": [
    "#BrainBinge",
    "#NeuralNetworks",
    "#AI"
  ],
  "processing_info": {
    "processed_at": "2025-11-12T14:30:22Z",
    "processing_time_seconds": 147.5
  }
}
```

## Temporary Files (`temp/`)

Intermediate files created during processing:

```
temp/
├── {job_id}/
│   ├── audio.wav              # Extracted audio (16kHz mono)
│   ├── alignment.json         # Force alignment results
│   ├── captions.srt           # Generated captions
│   ├── styled_captions.ass    # Styled captions
│   ├── broll_plan.json        # B-roll insertion plan
│   ├── broll/                 # Downloaded B-roll clips
│   ├── composed.mp4           # Composed video (pre-encoding)
│   └── logs/                  # Processing logs
```

**Cleanup:** Temporary files are automatically deleted after successful processing unless `KEEP_TEMP_FILES=true` in `.env`.

## File Naming Conventions

### Input Files
- **Videos:** `{topic}_{duration}_{version}.mp4`
  - Examples: `neural_networks_60s_v1.mp4`, `quantum_physics_90s_final.mp4`

- **Scripts:** Match video filename with appropriate extension
  - Examples: `neural_networks_60s_v1.txt`, `quantum_physics_90s_final.json`

### Output Files
- **Videos:** `{brand}_{timestamp}_{platform}.mp4`
- **Captions:** `{brand}_{timestamp}_{platform}.srt`
- **Metadata:** `{brand}_{timestamp}_{platform}_metadata.json`
- **Thumbnails:** `{brand}_{timestamp}_{platform}_thumb.jpg`

## Getting Sample Data

### Option 1: Create Your Own
1. Generate video on [HeyGen](https://www.heygen.com)
2. Download MP4 file
3. Export script as text
4. Place in `data/input/`

### Option 2: Use Test Data
```bash
# Download sample files (when available)
curl -o data/input/sample_video.mp4 https://example.com/sample_video.mp4
curl -o data/input/sample_script.txt https://example.com/sample_script.txt
```

### Option 3: Generate Mock Data
```bash
# Generate test script
cat > data/input/test_script.txt <<EOF
This is a test video script.
It contains multiple sentences.
Each sentence will be processed separately.
EOF
```

## Storage Recommendations

### Development
- Keep 2-3 sample videos locally (< 100 MB total)
- Store in `data/input/`
- Add sample files to `.gitignore`

### Production
- **Input:** Cloud storage (S3, GCS, Azure Blob)
- **Output:** Cloud storage with CDN
- **Temp:** Local SSD or fast cloud storage
- **Archive:** Glacier/Coldline for long-term storage

## Usage Examples

### Process Single Video
```bash
heygen-clipper process \
  --video data/input/sample_video.mp4 \
  --script data/input/sample_script.txt \
  --config config/brand.yaml \
  --output data/output/
```

### Batch Processing
```bash
# Process all videos in input directory
heygen-clipper batch \
  --input-dir data/input \
  --config config/brand.yaml \
  --output-dir data/output
```

### Validation
```bash
# Validate files before processing
heygen-clipper validate \
  --video data/input/sample_video.mp4 \
  --script data/input/sample_script.txt \
  --config config/brand.yaml
```

## Disk Space Management

### Estimating Space Requirements

**Per 60-second video:**
- Input video: 10-50 MB
- Temp files: 50-200 MB (during processing)
- Output per platform: 8-15 MB
- Total peak: ~300 MB

**For 100 videos:**
- Input: 5 GB
- Output (3 platforms): 3.6 GB
- Temp (peak): 20 GB
- **Total recommended:** 30-50 GB

### Cleanup Commands

```bash
# Clean temporary files
rm -rf data/temp/*

# Clean old outputs (older than 30 days)
find data/output -type f -mtime +30 -delete

# Using Makefile
make clean-data  # Interactive prompt before deletion
```

### Automated Cleanup (Cron)

```bash
# Add to crontab
# Clean temp files daily at 2 AM
0 2 * * * find /path/to/data/temp -mtime +1 -delete

# Clean old outputs weekly
0 3 * * 0 find /path/to/data/output -mtime +30 -delete
```

## Troubleshooting

### Common Issues

**Error: "Video file not found"**
```bash
# Check file exists
ls -lh data/input/sample_video.mp4

# Use absolute paths
heygen-clipper process --video $(pwd)/data/input/sample_video.mp4 ...
```

**Error: "Invalid video format"**
```bash
# Check video codec
ffprobe data/input/sample_video.mp4

# Convert to supported format
ffmpeg -i input.mov -c:v libx264 -c:a aac output.mp4
```

**Error: "Disk space full"**
```bash
# Check available space
df -h data/

# Clean temp files
rm -rf data/temp/*
```

## Best Practices

1. **Organization**
   - Use descriptive filenames
   - Group related files together
   - Maintain consistent naming conventions

2. **Version Control**
   - DO NOT commit large video files
   - DO commit sample scripts and configs
   - Use `.gitignore` for outputs

3. **Backup**
   - Backup input files to cloud storage
   - Keep processed outputs for 30 days
   - Archive important videos long-term

4. **Security**
   - Do not commit sensitive client data
   - Sanitize metadata in outputs
   - Use environment variables for API keys

## File Size Limits

### Platform Maximums
- **Instagram Reels:** 500 MB
- **TikTok:** 287 MB (iOS) / 72 MB (Android)
- **YouTube Shorts:** 256 GB (but keep under 100 MB)

### Recommended Output Sizes
- **Instagram:** 10-15 MB for 60s video
- **TikTok:** 8-12 MB for 60s video
- **YouTube:** 12-18 MB for 60s video

## Support

For questions about data formats:
- **Documentation:** See [API_SPEC.md](../API_SPEC.md)
- **Issues:** [GitHub Issues](https://github.com/yourusername/heygen-social-clipper/issues)
- **Email:** support@brainbinge.com

---

**Last Updated:** 2025-11-12
**Version:** 0.1.0-alpha
