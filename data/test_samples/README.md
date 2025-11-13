# Test Samples Directory

This directory contains sample HeyGen videos and their associated scripts for testing the video processing pipeline.

## Directory Structure

```
data/test_samples/
├── sample_01/
│   ├── video.mp4           # Original HeyGen video
│   ├── script.txt          # Full script/transcript
│   ├── metadata.json       # Video metadata (duration, resolution, etc.)
│   └── expected_output/    # Expected outputs for validation
│       ├── audio.wav       # Expected Stage 1 output
│       ├── alignment.json  # Expected Stage 2 output
│       └── captions.srt    # Expected Stage 3 output
├── sample_02/
│   └── ...
└── README.md               # This file
```

## What to Include

For each test sample, provide:

### 1. Video File (`video.mp4`)
- **Source**: Raw HeyGen-generated video
- **Format**: MP4 (H.264)
- **Duration**: 30-60 seconds recommended for quick tests
- **Resolution**: 1080p or 1920x1080
- **Note**: Keep file size reasonable (<50MB if possible)

### 2. Script File (`script.txt`)
The exact script used to generate the HeyGen video. Format:
```
This is the complete script that was used to generate the video.
Include all text exactly as spoken in the video.
Each sentence or paragraph should be on its own line.
```

### 3. Metadata File (`metadata.json`)
```json
{
  "title": "Sample Marketing Video",
  "description": "Brief description of the video content",
  "duration_seconds": 45.5,
  "resolution": "1920x1080",
  "fps": 30,
  "heygen_avatar": "avatar_name",
  "created_date": "2025-01-15",
  "target_platform": "TikTok",
  "notes": "Any special notes about this sample"
}
```

### 4. Brand Config (Optional) (`brand.yaml`)
```yaml
brand:
  name: "BrainBinge"
  colors:
    primary: "#FF6B6B"
    secondary: "#4ECDC4"
    background: "#1A1A2E"

captions:
  font_family: "Montserrat"
  font_size: 48
  position: "bottom"
  style: "word_highlight"
```

## Adding Your Test Sample

### Step 1: Create a Sample Directory
```bash
mkdir -p data/test_samples/sample_01
cd data/test_samples/sample_01
```

### Step 2: Add Your Files
```bash
# Copy your HeyGen video
cp /path/to/your/heygen_video.mp4 video.mp4

# Create the script file
nano script.txt
# Paste your script and save
```

### Step 3: Create Metadata
```bash
# Create metadata.json
cat > metadata.json << 'EOF'
{
  "title": "Your Video Title",
  "description": "Description",
  "duration_seconds": 45.0,
  "resolution": "1920x1080",
  "fps": 30,
  "target_platform": "TikTok"
}
EOF
```

### Step 4: Verify
```bash
# Check all files are present
ls -lh
# Should show: video.mp4, script.txt, metadata.json
```

## Using Test Samples

### Manual Testing
```bash
# Process a test sample
heygen-clipper process \
  --video data/test_samples/sample_01/video.mp4 \
  --script data/test_samples/sample_01/script.txt \
  --output data/output/test_sample_01.mp4 \
  --platform tiktok

# Batch process all samples
heygen-clipper batch \
  --input-dir data/test_samples \
  --output-dir data/output/tests
```

### Automated Testing
```bash
# Run integration tests with test samples
pytest tests/integration/test_pipeline.py -v

# Run with specific sample
pytest tests/integration/test_pipeline.py::test_full_pipeline[sample_01] -v
```

## Git LFS (Large File Storage)

Video files are large. We have two options:

### Option 1: Keep Local Only (Recommended for Now)
Test samples are already in `.gitignore` and won't be committed to git.

### Option 2: Use Git LFS (For Team Sharing)
```bash
# Install Git LFS
brew install git-lfs
git lfs install

# Track video files
git lfs track "data/test_samples/**/*.mp4"
git lfs track "data/test_samples/**/*.wav"

# Commit LFS configuration
git add .gitattributes
git commit -m "Configure Git LFS for test samples"
```

## File Size Guidelines

- **Small test** (<10MB): Good for quick unit tests
- **Medium test** (10-50MB): Good for integration tests
- **Large test** (50-200MB): Use for full pipeline validation
- **Avoid** (>200MB): Too large, use shorter clips

## Privacy & Licensing

⚠️ **Important**: Only include test samples that:
- You have rights to use
- Don't contain sensitive information
- Are appropriate for public repositories (if sharing)

## Examples Needed

Ideal test coverage should include:
- [ ] Short video (15-30 seconds)
- [ ] Medium video (45-60 seconds)
- [ ] Video with fast speech
- [ ] Video with slow/clear speech
- [ ] Video with technical terms
- [ ] Video with background music
- [ ] Vertical format (9:16 for TikTok/Instagram)
- [ ] Horizontal format (16:9 for YouTube)

## Validation

After adding a test sample, verify:
```bash
# Check video is playable
ffmpeg -i data/test_samples/sample_01/video.mp4

# Check duration
ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 \
  data/test_samples/sample_01/video.mp4

# Count words in script
wc -w data/test_samples/sample_01/script.txt
```

---

**Last Updated**: 2025-01-15
