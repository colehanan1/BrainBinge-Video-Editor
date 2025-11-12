# Contributing to HeyGen Social Clipper

Thank you for your interest in contributing to HeyGen Social Clipper! This document provides guidelines and standards for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Community](#community)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, background, or identity.

### Our Standards

**Positive behaviors:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behaviors:**
- Harassment, trolling, or discriminatory comments
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.9 or higher
- Git installed and configured
- FFmpeg installed (for video processing)
- Basic understanding of video processing concepts
- Familiarity with Click (CLI framework) and pytest

### Setting Up Development Environment

1. **Fork and Clone**

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/heygen-social-clipper.git
cd heygen-social-clipper
```

2. **Create Virtual Environment**

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

3. **Install Dependencies**

```bash
# Install package in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
```

4. **Configure Environment**

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

5. **Verify Installation**

```bash
# Run tests to verify setup
make test

# Check code style
make lint
```

## Development Workflow

### Branch Naming Convention

Use descriptive branch names following this pattern:

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Urgent fixes for production
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates
- `test/description` - Test additions or modifications

**Examples:**
```
feature/add-tiktok-export
bugfix/caption-timing-issue
docs/update-api-spec
test/add-broll-integration-tests
```

### Commit Message Guidelines

Follow the Conventional Commits specification:

**Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, etc.)
- `refactor` - Code refactoring
- `test` - Test additions or modifications
- `chore` - Maintenance tasks
- `perf` - Performance improvements

**Examples:**

```
feat(captions): add word-level highlighting animation

- Implement frame-by-frame text color changes
- Add configuration options for highlight duration
- Update caption styling engine

Closes #42
```

```
fix(broll): resolve Pexels API timeout errors

- Add retry logic with exponential backoff
- Implement request timeout configuration
- Add fallback to local library on API failure

Fixes #58
```

### Making Changes

1. **Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**
   - Write clean, documented code
   - Follow coding standards (see below)
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_your_feature.py

# Check coverage
make coverage
```

4. **Lint your code**
```bash
# Check code style
make lint

# Auto-format code
make format
```

5. **Commit your changes**
```bash
git add .
git commit -m "feat(module): description of changes"
```

6. **Push to your fork**
```bash
git push origin feature/your-feature-name
```

## Coding Standards

### Python Style Guide

Follow PEP 8 with these specifics:

**Line Length:**
- Maximum 100 characters per line
- Use implicit line continuation inside parentheses

**Imports:**
```python
# Standard library imports
import os
import sys
from typing import List, Dict, Optional

# Third-party imports
import click
import yaml
from moviepy.editor import VideoFileClip

# Local imports
from heygen_clipper.utils import validate_file
from heygen_clipper.config import load_config
```

**Naming Conventions:**
- `snake_case` for functions and variables
- `PascalCase` for classes
- `UPPER_CASE` for constants
- Prefix private methods with single underscore `_method_name`

**Type Hints:**
Use type hints for all function signatures:

```python
def process_video(
    video_path: str,
    script_path: str,
    config: Dict[str, Any],
    output_dir: str
) -> Dict[str, str]:
    """
    Process a HeyGen video into social media content.

    Args:
        video_path: Path to input video file
        script_path: Path to script JSON/SRT file
        config: Brand configuration dictionary
        output_dir: Output directory path

    Returns:
        Dictionary mapping platforms to output file paths

    Raises:
        ValueError: If input files are invalid
        ProcessingError: If video processing fails
    """
    # Implementation
    pass
```

**Docstrings:**
Use Google-style docstrings for all public functions and classes:

```python
class CaptionGenerator:
    """Generates and styles captions for videos.

    This class handles caption generation from script files,
    applies brand styling, and synchronizes text with video timing.

    Attributes:
        config: Brand configuration dictionary
        font_path: Path to custom font file

    Example:
        >>> generator = CaptionGenerator(config)
        >>> captions = generator.generate(script, video_clip)
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize caption generator.

        Args:
            config: Brand configuration containing font and style settings
        """
        pass
```

### Code Organization

**Module Structure:**
```python
# Module docstring
"""
Caption generation and styling module.

This module provides functionality for generating synchronized captions
and applying brand-specific styling to video content.
"""

# Imports
import os
from typing import List, Dict

# Constants
DEFAULT_FONT_SIZE = 48
MAX_CAPTION_LENGTH = 100

# Classes
class CaptionGenerator:
    pass

# Functions
def parse_script(script_path: str) -> List[Dict]:
    pass

# Main execution (if applicable)
if __name__ == "__main__":
    pass
```

### Error Handling

Use specific exceptions and provide helpful error messages:

```python
# Define custom exceptions
class VideoProcessingError(Exception):
    """Raised when video processing fails."""
    pass

class InvalidConfigError(Exception):
    """Raised when configuration is invalid."""
    pass

# Use exceptions appropriately
def load_video(video_path: str) -> VideoFileClip:
    """Load video file and validate."""
    if not os.path.exists(video_path):
        raise FileNotFoundError(
            f"Video file not found: {video_path}"
        )

    try:
        clip = VideoFileClip(video_path)
    except Exception as e:
        raise VideoProcessingError(
            f"Failed to load video {video_path}: {str(e)}"
        ) from e

    return clip
```

## Testing Requirements

### Test Coverage

- Minimum 80% code coverage required
- All new features must include tests
- Bug fixes must include regression tests
- Critical paths require 100% coverage

### Writing Tests

**Test File Structure:**
```python
"""
Tests for caption generation module.
"""
import pytest
from heygen_clipper.captions import CaptionGenerator

class TestCaptionGenerator:
    """Test suite for CaptionGenerator class."""

    @pytest.fixture
    def config(self):
        """Provide test configuration."""
        return {
            'captions': {
                'font': {'family': 'Arial', 'size': 48},
                'style': {'color': '#FFFFFF'}
            }
        }

    @pytest.fixture
    def generator(self, config):
        """Provide CaptionGenerator instance."""
        return CaptionGenerator(config)

    def test_initialization(self, generator):
        """Test generator initializes correctly."""
        assert generator is not None
        assert generator.font_size == 48

    def test_caption_generation(self, generator):
        """Test caption generation from script."""
        script = [
            {'start': 0.0, 'end': 3.0, 'text': 'Hello world'}
        ]
        captions = generator.generate(script)
        assert len(captions) == 1
        assert captions[0]['text'] == 'Hello world'

    def test_invalid_script_raises_error(self, generator):
        """Test error handling for invalid script."""
        with pytest.raises(ValueError):
            generator.generate(None)
```

**Test Categories:**

1. **Unit Tests** - Test individual functions and methods
2. **Integration Tests** - Test module interactions
3. **End-to-End Tests** - Test complete workflows
4. **Performance Tests** - Test processing speed and resource usage

**Running Tests:**
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_captions.py

# Run specific test
pytest tests/test_captions.py::TestCaptionGenerator::test_generation

# Run with coverage
pytest --cov=heygen_clipper --cov-report=html

# Run only fast tests (skip slow integration tests)
pytest -m "not slow"
```

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_parse_script():
    """Unit test for script parsing."""
    pass

@pytest.mark.integration
def test_full_pipeline():
    """Integration test for complete pipeline."""
    pass

@pytest.mark.slow
def test_video_processing():
    """Slow test requiring video encoding."""
    pass
```

## Documentation

### Code Documentation

- All public functions, classes, and methods must have docstrings
- Use Google-style docstrings
- Include examples for complex functions
- Document all parameters and return values
- Note any exceptions that may be raised

### README Updates

When adding new features:
- Update README.md with usage examples
- Add to the appropriate section
- Update table of contents if needed

### API Documentation

When changing CLI commands or configurations:
- Update API_SPEC.md
- Document new options and flags
- Provide examples
- Update version history

## Pull Request Process

### Before Submitting

**Checklist:**
- [ ] All tests pass (`make test`)
- [ ] Code follows style guidelines (`make lint`)
- [ ] Code coverage is ≥ 80% (`make coverage`)
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Commit messages follow conventions
- [ ] Branch is up-to-date with main

### Submitting Pull Request

1. **Create Pull Request**
   - Use a descriptive title
   - Reference related issues
   - Provide detailed description of changes
   - Include screenshots/videos for UI changes

2. **Pull Request Template**

```markdown
## Description
Brief description of changes and motivation.

## Related Issues
Fixes #123
Relates to #456

## Changes Made
- Added feature X
- Fixed bug Y
- Refactored module Z

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Screenshots/Videos
(if applicable)

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

3. **Review Process**
   - Address reviewer feedback promptly
   - Keep discussions professional and constructive
   - Make requested changes in new commits
   - Squash commits before final merge (if requested)

### Review Criteria

Pull requests are evaluated on:
- Code quality and style compliance
- Test coverage and quality
- Documentation completeness
- Performance impact
- Breaking changes (require major version bump)

## Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
## Bug Description
Clear and concise description of the bug.

## Steps to Reproduce
1. Run command '...'
2. With configuration '...'
3. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.10.5]
- HeyGen Clipper version: [e.g., 1.0.0]
- FFmpeg version: [e.g., 4.4.2]

## Additional Context
- Configuration files
- Error logs
- Screenshots
```

### Feature Requests

Use the feature request template:

```markdown
## Feature Description
Clear description of the proposed feature.

## Use Case
Why is this feature needed? Who will benefit?

## Proposed Solution
How should this feature work?

## Alternatives Considered
Other approaches you've considered.

## Additional Context
Mockups, examples, references.
```

## Community

### Communication Channels

- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - Questions and general discussion
- **Pull Requests** - Code review and technical discussion

### Getting Help

- Check existing issues and documentation first
- Search discussions for similar questions
- Provide detailed context when asking questions
- Be patient and respectful

### Recognition

Contributors are recognized in:
- CHANGELOG.md for each release
- GitHub contributors page
- Release notes

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

**Thank you for contributing to HeyGen Social Clipper!**

If you have questions about contributing, please open a discussion on GitHub.
