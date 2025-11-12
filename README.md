# HeyGen Social Clipper

> Transform HeyGen AI videos into viral social media content automatically

## Project Summary

HeyGen Social Clipper is a Python CLI tool designed to automate the transformation of HeyGen-generated videos into optimized, branded social media content for Instagram Reels, TikTok, and YouTube Shorts. The tool processes raw HeyGen videos alongside scripts and branding configurations to produce viral-ready vertical video content with professional overlays, B-roll integration, captions, and platform-specific optimizations.

### Mission

Eliminate the manual video editing bottleneck in content production by automating the entire post-production pipeline from HeyGen output to platform-ready social videos.

### How It Works

The system receives:
- Raw HeyGen video (MP4, 1080x1920, 24fps)
- Video script (JSON with timestamps and text)
- Configuration file (branding, B-roll, music preferences)
- Optional webhook trigger from Make.com automation

It outputs:
- Platform-optimized vertical videos (9:16 aspect ratio)
- Burned-in captions with brand styling
- Integrated B-roll footage and branded overlays
- Background music and audio enhancement
- Metadata files for social media posting

## 7-Stage Processing Pipeline

The HeyGen Social Clipper implements a comprehensive video processing pipeline:

### 1. **Input Ingestion & Validation**
   - Parse video files, scripts (JSON/SRT), and config (YAML/JSON)
   - Validate file formats, resolution, frame rates
   - Check for required fields and data integrity
   - Generate processing manifest

### 2. **Script Analysis & Scene Planning**
   - Parse timestamps and text segments from script
   - Identify key moments, transitions, and emphasis points
   - Plan B-roll insertion points based on content analysis
   - Calculate optimal scene durations for platform engagement

### 3. **Video Composition & Framing**
   - Ensure 9:16 aspect ratio (1080x1920)
   - Apply speaker framing and positioning
   - Integrate branded overlays (logo, watermarks)
   - Implement visual hierarchy for multi-element scenes

### 4. **B-Roll Integration**
   - Source B-roll from local library or Pexels API
   - Match B-roll to script keywords and context
   - Blend B-roll with main footage using transitions
   - Maintain visual coherence and pacing

### 5. **Caption Generation & Styling**
   - Generate word-level synchronized captions
   - Apply brand typography, colors, and animations
   - Implement dynamic text effects (highlights, emphasis)
   - Ensure readability across all platforms

### 6. **Audio Enhancement**
   - Add background music from library
   - Balance audio levels (voice, music, effects)
   - Apply audio normalization and compression
   - Ensure platform-specific audio compliance

### 7. **Export & Platform Optimization**
   - Render final video with optimal codec settings
   - Generate platform-specific versions (Instagram, TikTok, YouTube)
   - Create metadata files with suggested captions and hashtags
   - Package output for immediate publishing

## Input/Output Overview

### Inputs

| Input Type | Format | Description |
|------------|--------|-------------|
| HeyGen Video | MP4 (1080x1920, 24fps) | Raw AI-generated video |
| Script | JSON/SRT | Timestamped transcript with text segments |
| Config | YAML/JSON | Branding, B-roll preferences, music, styling |
| Webhook | HTTP POST | Optional Make.com trigger with metadata |

### Outputs

| Output Type | Format | Description |
|-------------|--------|-------------|
| Final Video | MP4 (H.264/H.265) | Platform-ready social video |
| Captions | SRT/VTT | Standalone caption files |
| Metadata | JSON | Publishing metadata, hashtags, descriptions |
| Thumbnail | JPG/PNG | Auto-generated thumbnail options |
| Processing Log | JSON | Detailed processing report and analytics |

### Example Output Specifications

**Instagram Reels / TikTok:**
- Resolution: 1080x1920 (9:16)
- Frame Rate: 30fps
- Codec: H.264, High Profile
- Bitrate: 8-12 Mbps
- Max Duration: 90 seconds
- Audio: AAC, 128-192 kbps

**YouTube Shorts:**
- Resolution: 1080x1920 (9:16)
- Frame Rate: 30fps
- Codec: H.264 or H.265
- Bitrate: 10-15 Mbps
- Max Duration: 60 seconds
- Audio: AAC, 192 kbps

## Technology Stack

### Core Video Processing
- **MoviePy** - Primary video editing and composition framework
  - *Rationale:* Python-native, extensive API, excellent for automation
- **FFmpeg** - Low-level encoding, transcoding, filtering
  - *Rationale:* Industry standard, maximum format support, high performance
- **OpenCV** - Computer vision, frame analysis, face detection
  - *Rationale:* Advanced visual processing, speaker framing, motion tracking

### Media Asset Management
- **Pexels API** - B-roll stock footage sourcing
  - *Rationale:* Free tier, extensive library, keyword search
- **Pillow (PIL)** - Image processing for overlays and thumbnails
  - *Rationale:* Standard Python library, broad format support

### Caption & Text Processing
- **Whisper (OpenAI)** - Backup audio-to-text transcription
  - *Rationale:* State-of-the-art accuracy, multiple language support
- **pysrt / webvtt-py** - Caption file parsing and generation
  - *Rationale:* Standard format compliance, timestamp handling

### Audio Processing
- **pydub** - Audio manipulation, mixing, normalization
  - *Rationale:* Simple API, format flexibility, FFmpeg integration

### Configuration & Workflow
- **PyYAML** - Configuration file parsing
  - *Rationale:* Human-readable configs, nested structure support
- **Click** - CLI framework for command-line interface
  - *Rationale:* Robust argument parsing, subcommand support, help generation
- **python-dotenv** - Environment variable management
  - *Rationale:* Secure API key handling, environment separation

### Testing & Quality
- **pytest** - Unit and integration testing
  - *Rationale:* Industry standard, fixture support, extensive plugins
- **pytest-cov** - Code coverage reporting
  - *Rationale:* Quality metrics, test completeness verification

### Utilities
- **requests** - HTTP client for webhook and API calls
  - *Rationale:* Standard library for external integrations
- **jsonschema** - Input validation and schema enforcement
  - *Rationale:* Robust validation, clear error messages

## Reused vs. Custom Components

### Reused (Leveraging Existing Libraries)
- Video encoding/decoding (FFmpeg, MoviePy)
- Audio processing pipeline (pydub, FFmpeg)
- Stock footage API integration (Pexels SDK)
- Caption file format handling (pysrt, webvtt-py)
- Speech recognition (Whisper API)
- CLI framework (Click)

### Custom-Built (Proprietary Logic)
- **Scene Planning Algorithm** - Intelligent B-roll insertion and timing
- **Brand Styling Engine** - Dynamic caption styling and overlay positioning
- **Content Analyzer** - Script-to-B-roll keyword matching
- **Multi-Platform Optimizer** - Platform-specific export profiles
- **Webhook Integration Layer** - Make.com automation bridge
- **Processing Pipeline Orchestrator** - Stage coordination and error handling
- **Configuration Schema** - Custom YAML/JSON format for brand settings

## Integration Architecture

### Make.com Webhook Flow

The tool supports automated triggering via Make.com webhooks:

1. **HeyGen Video Generated** → Trigger Make.com scenario
2. **Make.com** → Downloads video, script, and config from cloud storage
3. **Make.com** → POSTs webhook to CLI tool with file paths
4. **CLI Tool** → Processes video through 7-stage pipeline
5. **CLI Tool** → Outputs final videos to designated folder
6. **Make.com** → Uploads to social media platforms
7. **Make.com** → Sends notifications and analytics

### CLI Workflow (Manual Execution)

```bash
# Single video processing
heygen-clipper process \
  --video path/to/heygen_video.mp4 \
  --script path/to/script.json \
  --config path/to/brand_config.yaml \
  --output path/to/output_folder

# Batch processing
heygen-clipper batch \
  --input-dir path/to/videos \
  --config path/to/brand_config.yaml \
  --output-dir path/to/outputs

# Watch mode (auto-process new files)
heygen-clipper watch \
  --watch-dir path/to/incoming \
  --config path/to/brand_config.yaml \
  --output-dir path/to/outputs
```

## MVP Timeline & Success Metrics

### Development Phases

**Phase 1: Foundation (Weeks 1-2)**
- Repository setup and documentation
- Core pipeline skeleton
- Input validation and config parsing
- Basic video ingestion

**Phase 2: Core Processing (Weeks 3-5)**
- Video composition and framing
- Caption generation and styling
- Basic B-roll integration
- Audio mixing

**Phase 3: Platform Optimization (Week 6)**
- Multi-platform export profiles
- Quality optimization
- Metadata generation

**Phase 4: Integration & Polish (Week 7-8)**
- Webhook integration
- Error handling and logging
- Testing and documentation
- Performance optimization

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Processing Time | < 3 minutes per 60s video | Automated timing logs |
| Output Quality | 95% pass rate (manual review) | QA checklist scoring |
| Platform Compliance | 100% upload success | API response tracking |
| Error Rate | < 2% processing failures | Exception monitoring |
| User Satisfaction | 4.5/5 stars | User feedback surveys |
| Code Coverage | > 80% | pytest-cov reports |

## Testing Strategy

### Unit Tests
- Individual module functionality (parsers, validators, processors)
- Configuration loading and validation
- Caption timing and synchronization
- File I/O operations

### Integration Tests
- End-to-end pipeline execution
- Multi-stage data flow
- External API interactions (mocked)
- Webhook payload handling

### Quality Assurance
- Manual video output review (visual quality, audio sync)
- Platform upload verification
- Edge case testing (missing files, invalid formats, corrupted data)
- Performance benchmarking (processing time, resource usage)

### Test Data
- Sample HeyGen videos (various durations, content types)
- Mock scripts (edge cases: long/short, special characters)
- Test configurations (minimal, maximal, invalid)
- Reference output videos (expected results)

## Reference Documentation

For detailed technical specifications and analysis:

- **[spec_document.md](docs/spec_document.md)** - Complete technical specification and requirements
- **[code_discovery_analysis.md](docs/code_discovery_analysis.md)** - Technology evaluation and architecture decisions
- **[API_SPEC.md](API_SPEC.md)** - CLI command reference and API documentation
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide

## Getting Started

### Prerequisites

- Python 3.9 or higher
- FFmpeg installed and available in PATH
- API keys for external services (Pexels, optional Whisper)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/heygen-social-clipper.git
cd heygen-social-clipper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Quick Start

```bash
# Validate your installation
heygen-clipper --version

# Process a sample video
heygen-clipper process \
  --video data/sample_video.mp4 \
  --script data/sample_script.json \
  --config data/sample_config.yaml \
  --output output/
```

## Project Structure

```
heygen-social-clipper/
├── src/                    # Business logic modules
│   ├── __init__.py
│   ├── cli.py             # CLI interface (Click commands)
│   ├── pipeline.py        # Pipeline orchestrator
│   ├── ingestion.py       # Input validation and parsing
│   ├── analyzer.py        # Script analysis and scene planning
│   ├── compositor.py      # Video composition and framing
│   ├── broll.py           # B-roll integration logic
│   ├── captions.py        # Caption generation and styling
│   ├── audio.py           # Audio enhancement
│   ├── exporter.py        # Platform-specific export
│   └── utils.py           # Shared utilities
├── tests/                 # Unit and integration tests
│   ├── __init__.py
│   ├── test_ingestion.py
│   ├── test_analyzer.py
│   ├── test_compositor.py
│   └── test_pipeline.py
├── data/                  # Sample inputs and test data
│   ├── README.txt         # Data directory guide
│   ├── sample_video.mp4   # (to be added)
│   ├── sample_script.json # (to be added)
│   └── sample_config.yaml # (to be added)
├── docs/                  # Architecture and specification docs
│   ├── spec_document.md   # (to be added)
│   └── code_discovery_analysis.md  # (to be added)
├── README.md              # This file
├── API_SPEC.md            # CLI and API reference
├── CONTRIBUTING.md        # Contribution guidelines
├── DEPLOYMENT.md          # Deployment instructions
├── CHANGELOG.md           # Version history
├── requirements.txt       # Python dependencies
├── setup.py               # Package configuration
├── Makefile               # Build and test automation
├── .gitignore             # Git ignore patterns
└── .env.example           # Environment variable template
```

## Contributing

We welcome contributions from the community! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Code style guidelines
- Testing requirements
- Pull request process
- Issue reporting standards

### Quick Contribution Checklist

- [ ] Fork the repository and create a feature branch
- [ ] Write tests for new functionality
- [ ] Ensure all tests pass (`make test`)
- [ ] Follow PEP 8 style guidelines
- [ ] Update documentation as needed
- [ ] Submit a pull request with clear description

## License

This project is licensed under the MIT License - see the LICENSE file for details.

Compatible with:
- MIT License
- Apache License 2.0
- BSD Licenses

## Contact & Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/heygen-social-clipper/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/heygen-social-clipper/discussions)
- **Email:** support@brainbinge.com

## Acknowledgments

- HeyGen for AI video generation technology
- Pexels for stock footage API
- Open source community for video processing libraries

---

**Status:** 🚧 Initial Repository Bootstrap - No code implementation yet

**Version:** 0.1.0-alpha

**Last Updated:** 2025-11-12
