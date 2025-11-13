"""
Configuration Loader Utility

Loads and validates configuration files with environment variable injection
and schema validation.

Example:
    >>> from src.utils.config_loader import load_config_with_env
    >>> config = load_config_with_env("config/brand.yaml")
    >>> print(config.get('pexels_api_key'))
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


def load_config_with_env(
    config_path: Path,
    env_file: Optional[Path] = None,
    validate: bool = True
) -> Dict[str, Any]:
    """
    Load configuration file and inject environment variables.

    Args:
        config_path: Path to configuration file (JSON/YAML)
        env_file: Optional path to .env file
        validate: Whether to validate required fields

    Returns:
        Configuration dictionary with injected environment variables

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If validation fails

    Example:
        >>> config = load_config_with_env(Path("config/brand.yaml"))
        >>> api_key = config.get('pexels_api_key')
    """
    # Load environment variables from .env file
    if env_file and env_file.exists():
        load_dotenv(env_file)
    else:
        # Try to load from default location
        default_env = Path('.env')
        if default_env.exists():
            load_dotenv(default_env)

    # Check if file exists
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    # Load configuration based on file extension
    suffix = config_path.suffix.lower()

    if suffix in ['.yaml', '.yml']:
        config = _load_yaml(config_path)
    elif suffix == '.json':
        config = _load_json(config_path)
    else:
        raise ValueError(
            f"Unsupported config format: {suffix}. "
            "Supported formats: .yaml, .yml, .json"
        )

    # Inject environment variables
    config = _inject_env_vars(config)

    # Validate if requested
    if validate:
        _validate_config(config)

    logger.debug(f"Loaded configuration from {config_path}")
    return config


def _load_yaml(path: Path) -> Dict[str, Any]:
    """Load YAML configuration file."""
    try:
        import yaml
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        raise ImportError(
            "PyYAML is required to load YAML configs. "
            "Install it with: pip install pyyaml"
        )
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {path}: {e}")


def _load_json(path: Path) -> Dict[str, Any]:
    """Load JSON configuration file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")


def _inject_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inject environment variables into configuration.

    Common environment variables:
    - PEXELS_API_KEY: API key for Pexels B-roll fetching
    - WEBHOOK_SECRET: Secret for webhook authentication
    - LOG_LEVEL: Logging level
    """
    # Inject API keys
    if 'pexels' not in config:
        config['pexels'] = {}

    config['pexels']['api_key'] = os.getenv(
        'PEXELS_API_KEY',
        config.get('pexels', {}).get('api_key', '')
    )

    # Inject webhook secret
    if 'webhook' not in config:
        config['webhook'] = {}

    config['webhook']['secret'] = os.getenv(
        'WEBHOOK_SECRET',
        config.get('webhook', {}).get('secret', '')
    )

    # Inject log level
    config['log_level'] = os.getenv(
        'LOG_LEVEL',
        config.get('log_level', 'INFO')
    )

    return config


def _validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration has required fields.

    Raises:
        ValueError: If required fields are missing
    """
    errors = []

    # Check for brand configuration (optional but recommended)
    if 'brand' not in config:
        logger.warning("No 'brand' section found in config (optional)")

    # Validate brand fields if present
    if 'brand' in config:
        brand = config['brand']
        recommended_fields = ['name', 'colors', 'fonts']
        missing = [f for f in recommended_fields if f not in brand]
        if missing:
            logger.warning(
                f"Recommended brand fields missing: {', '.join(missing)}"
            )

    # Check for caption styling (optional)
    if 'captions' not in config:
        logger.warning("No 'captions' section found in config (using defaults)")

    # Validate Pexels API key if B-roll is configured
    if config.get('broll', {}).get('enabled', True):
        if not config.get('pexels', {}).get('api_key'):
            logger.warning(
                "PEXELS_API_KEY not set - B-roll fetching will be skipped. "
                "Set it in .env file or config."
            )

    # Raise errors if any critical validations failed
    if errors:
        raise ValueError(
            f"Configuration validation failed:\n" + "\n".join(errors)
        )


def load_dotenv(env_path: Path) -> None:
    """
    Load environment variables from .env file.

    Args:
        env_path: Path to .env file

    Example:
        >>> load_dotenv(Path('.env'))
    """
    try:
        from dotenv import load_dotenv as _load_dotenv
        _load_dotenv(env_path)
        logger.debug(f"Loaded environment variables from {env_path}")
    except ImportError:
        logger.warning(
            "python-dotenv not installed. Install with: pip install python-dotenv"
        )
        # Fallback: manual parsing
        _manual_load_dotenv(env_path)


def _manual_load_dotenv(env_path: Path) -> None:
    """Manually parse and load .env file without python-dotenv."""
    if not env_path.exists():
        return

    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                # Set environment variable (don't override existing)
                if key not in os.environ:
                    os.environ[key] = value


def create_default_config(output_path: Path, format: str = 'yaml') -> None:
    """
    Create default configuration template.

    Args:
        output_path: Path to save configuration file
        format: Format ('yaml' or 'json')

    Example:
        >>> create_default_config(Path("config/mybrand.yaml"))
    """
    default_config = {
        'brand': {
            'name': 'My Brand',
            'colors': {
                'primary': '#FF6B6B',
                'secondary': '#4ECDC4',
                'text': '#FFFFFF',
            },
            'fonts': {
                'primary': 'Arial',
                'secondary': 'Helvetica',
            },
        },
        'captions': {
            'font_size': 28,
            'font_family': 'Arial',
            'position': 'bottom',
            'max_words_per_caption': 3,
            'min_caption_duration_ms': 200,
        },
        'video': {
            'resolution': '1280x720',
            'fps': 30,
            'bitrate': '5000k',
        },
        'broll': {
            'enabled': True,
            'cache_dir': 'data/cache/broll',
        },
        'pexels': {
            'api_key': '${PEXELS_API_KEY}',  # Set in .env
        },
        'encoding': {
            'codec': 'hevc_videotoolbox',
            'fallback_codec': 'libx264',
            'target_size_mb': 30,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format == 'yaml':
        try:
            import yaml
            with open(output_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
        except ImportError:
            raise ImportError("PyYAML required for YAML output. Install: pip install pyyaml")
    elif format == 'json':
        with open(output_path, 'w') as f:
            json.dump(default_config, f, indent=2)
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'yaml' or 'json'")

    logger.info(f"Created default configuration: {output_path}")
