HeyGen Social Clipper - Data Directory Guide
=============================================

This directory contains sample inputs, test data, and configuration examples
for the HeyGen Social Clipper project.

DIRECTORY STRUCTURE
-------------------

data/
├── README.txt              # This file
├── sample_video.mp4        # Sample HeyGen video (to be added)
├── sample_script.json      # Sample script file (to be added)
├── sample_config.yaml      # Sample brand configuration (to be added)
├── temp/                   # Temporary processing files (auto-created)
└── output/                 # Processed video output (auto-created)


WHAT TO PUT HERE
----------------

1. SAMPLE VIDEOS (sample_video.mp4)
   - HeyGen-generated MP4 videos
   - Recommended specs:
     * Resolution: 1080x1920 (9:16 vertical) or 1920x1080
     * Frame rate: 24fps or 30fps
     * Duration: 30-90 seconds
     * Codec: H.264
   - Use for testing and development
   - DO NOT commit large video files to git!

2. SAMPLE SCRIPTS (sample_script.json)
   - Timestamped transcript of video content
   - JSON format (preferred) or SRT format
   - Should match the sample video
   - Example structure:
     {
       "version": "1.0",
       "metadata": {
         "title": "Test Video",
         "duration": 60.0
       },
       "segments": [
         {
           "id": 1,
           "start": 0.0,
           "end": 3.5,
           "text": "Welcome to the video!",
           "broll_keywords": ["welcome", "greeting"]
         }
       ]
     }

3. SAMPLE CONFIGURATIONS (sample_config.yaml)
   - Brand configuration files
   - YAML format (preferred) or JSON format
   - Include branding elements:
     * Logo and watermark paths
     * Color schemes
     * Caption styling
     * B-roll preferences
     * Audio settings
     * Export settings
   - See API_SPEC.md for complete schema

4. TEST DATA
   - Multiple videos of varying lengths
   - Edge cases:
     * Very short videos (10-15 seconds)
     * Longer videos (2-3 minutes)
     * Different aspect ratios
     * Various quality levels
   - Scripts with edge cases:
     * Long text segments
     * Special characters
     * Multiple speakers
     * No timestamps (for testing)

5. ASSETS (optional subdirectories)
   - assets/broll/       # Local B-roll video clips
   - assets/music/       # Background music tracks
   - assets/logos/       # Brand logos and watermarks
   - assets/fonts/       # Custom fonts for captions


FOLDER USAGE
------------

temp/
  - Automatically created during processing
  - Stores intermediate files (frames, audio tracks, etc.)
  - Cleaned up after successful processing
  - Configure KEEP_TEMP_FILES=true in .env to preserve for debugging
  - DO NOT commit temp files to git

output/
  - Automatically created during processing
  - Stores final processed videos and metadata
  - Platform-specific outputs:
    * {name}_instagram.mp4
    * {name}_tiktok.mp4
    * {name}_youtube.mp4
    * {name}_{platform}.srt (captions)
    * {name}_{platform}_metadata.json
    * {name}_{platform}_thumb.jpg
  - DO NOT commit output files to git (unless specifically needed as reference)


FILE NAMING CONVENTIONS
-----------------------

Input Videos:
  - Use descriptive names: topic_duration_version.mp4
  - Examples:
    * neural_networks_60s_v1.mp4
    * quantum_physics_90s_final.mp4
    * marketing_basics_45s.mp4

Scripts:
  - Match video filename with .json or .srt extension
  - Examples:
    * neural_networks_60s_v1.json
    * quantum_physics_90s_final.srt

Configurations:
  - Describe brand or use case
  - Examples:
    * brainbinge_brand.yaml
    * client_acme_corp.yaml
    * test_minimal.yaml


GETTING SAMPLE DATA
-------------------

1. Create Your Own HeyGen Video:
   - Sign up at https://www.heygen.com
   - Generate a test video
   - Download in MP4 format
   - Export the script as JSON

2. Use Provided Examples (after implementation):
   - Sample files will be added to this directory
   - Check repository releases for test data packs

3. Generate Test Scripts:
   - Use the script template in API_SPEC.md
   - Create mock timestamps and text
   - Add B-roll keywords for testing


STORAGE RECOMMENDATIONS
-----------------------

Development:
  - Keep 2-3 sample videos locally
  - Total size: < 100 MB
  - Store in this directory

Testing:
  - Use separate test data repository
  - Link as git submodule if needed
  - Or download on-demand during CI/CD

Production:
  - Store input videos in cloud storage (S3, GCS, Azure Blob)
  - Stream directly from cloud URLs
  - Configure webhook to accept cloud URLs
  - Archive processed outputs to cloud storage


EXAMPLE WORKFLOW
----------------

1. Development Setup:
   $ mkdir -p data/temp data/output
   $ cp your_video.mp4 data/sample_video.mp4
   $ cp your_script.json data/sample_script.json
   $ cp config/brand.example.yaml data/sample_config.yaml

2. Test Processing:
   $ heygen-clipper process \
       --video data/sample_video.mp4 \
       --script data/sample_script.json \
       --config data/sample_config.yaml \
       --output data/output/

3. Review Output:
   $ ls data/output/
   $ open data/output/YourBrand_20251112_instagram.mp4


SECURITY NOTES
--------------

- DO NOT commit sensitive data (client videos, proprietary content)
- Use .gitignore to exclude *.mp4, *.mov, *.avi files
- Keep only reference/sample data in repository
- Use environment variables for API keys (never in config files)
- Encrypt sensitive configurations if committed


DATA CLEANUP
------------

Manual Cleanup:
  $ rm -rf data/temp/*
  $ rm -rf data/output/*

Using Makefile:
  $ make clean-data

Automated Cleanup (cron job):
  # Clean temp files older than 1 day
  0 0 * * * find /path/to/data/temp -mtime +1 -delete

  # Clean output files older than 7 days
  0 0 * * * find /path/to/data/output -mtime +7 -delete


TROUBLESHOOTING
---------------

Q: Video file not found error
A: Ensure video file exists and path is correct. Use absolute paths.

Q: Script format invalid
A: Validate JSON format with jsonlint or jq tool.
   $ cat sample_script.json | jq .

Q: Disk space error
A: Check available space:
   $ df -h data/
   Clean temp/output directories if needed.

Q: Permission denied
A: Ensure write permissions:
   $ chmod -R u+w data/


RESOURCES
---------

- API Specification: ../API_SPEC.md
- Configuration Examples: ../config/ (to be added)
- Video Format Guide: ../docs/video_formats.md (to be added)
- Script Format Reference: ../API_SPEC.md#script-file-format


CONTACT
-------

For questions about sample data formats:
- GitHub Issues: https://github.com/yourusername/heygen-social-clipper/issues
- Email: support@brainbinge.com


---

Last Updated: 2025-11-12
Version: 0.1.0-alpha
