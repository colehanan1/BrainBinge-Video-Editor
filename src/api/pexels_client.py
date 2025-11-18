"""
Pexels API Client

Client for searching and downloading B-roll footage from Pexels with intelligent
caching, rate limiting, and graceful error handling.

API Documentation: https://www.pexels.com/api/documentation/
Free Tier: 200 requests/hour

Example:
    >>> from src.api.pexels_client import BRollFetcher
    >>> fetcher = BRollFetcher(api_key="your_key")
    >>> clips = fetcher.fetch_from_plan("broll_plan.csv")
    >>> print(f"Downloaded {len(clips)} clips")
"""

import csv
import hashlib
import json
import logging
import requests
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PexelsAPIError(Exception):
    """Raised when Pexels API request fails."""
    pass


class BRollFetcher:
    """
    Download B-roll clips from Pexels API with smart caching and rate limiting.

    Handles:
    - CSV plan parsing
    - Pexels API search and download
    - Intelligent caching (MD5-based)
    - Rate limiting (200 requests/hour)
    - Graceful degradation on failures

    Args:
        api_key: Pexels API key from https://www.pexels.com/api/
        cache_dir: Directory for caching downloads (default: data/temp/broll_cache)
    """

    BASE_URL = "https://api.pexels.com/videos"
    RATE_LIMIT = 200  # Requests per hour
    RATE_WINDOW = 3600  # 1 hour in seconds

    def __init__(self, api_key: str, cache_dir: Optional[Path] = None):
        """
        Initialize Pexels B-roll fetcher.

        Args:
            api_key: Pexels API key
            cache_dir: Directory for caching (default: data/temp/broll_cache)
        """
        self.api_key = api_key
        self.cache_dir = cache_dir or Path("data/temp/broll_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Rate limiting state file
        self.rate_limit_file = self.cache_dir / "rate_limit.json"
        self._init_rate_limit()

    def fetch_from_plan(self, csv_path: Path) -> List[Dict[str, Any]]:
        """
        Download all B-roll clips specified in CSV plan.

        Args:
            csv_path: Path to broll_plan.csv with columns:
                - start_sec: Start time in seconds
                - end_sec: End time in seconds
                - type: "pip" or "fullframe"
                - search_query: Pexels search term
                - fade_in: Fade in duration (optional, default: 0.5)
                - fade_out: Fade out duration (optional, default: 0.5)

        Returns:
            List of clip dicts with local_path added:
            [{
                "start_time": 5.0,
                "end_time": 12.0,
                "type": "pip",
                "search_query": "team collaboration",
                "path": Path("/path/to/cached/video.mp4"),
                "fade_in": 0.5,
                "fade_out": 0.5
            }, ...]

        Raises:
            FileNotFoundError: If CSV file not found
            ValueError: If CSV has invalid format
        """
        logger.info(f"Loading B-roll plan from {csv_path}")

        # Parse CSV
        clips_plan = self._parse_csv(csv_path)
        logger.info(f"Found {len(clips_plan)} B-roll clips in plan")

        # Download each clip
        downloaded_clips = []
        for i, clip in enumerate(clips_plan, 1):
            query = clip["search_query"]
            duration_needed = clip["end_time"] - clip["start_time"]

            logger.info(f"[{i}/{len(clips_plan)}] Fetching B-roll: '{query}' ({duration_needed:.1f}s)")

            try:
                video_path = self.search_and_download(query, duration_needed)

                if video_path:
                    clip["path"] = video_path
                    downloaded_clips.append(clip)
                    logger.info(f"  ✓ Downloaded: {video_path.name}")
                else:
                    logger.warning(f"  ✗ Failed to download B-roll for '{query}' (skipping)")

            except Exception as e:
                logger.warning(f"  ✗ Error downloading B-roll for '{query}': {e} (skipping)")

        logger.info(f"Downloaded {len(downloaded_clips)}/{len(clips_plan)} B-roll clips")
        return downloaded_clips

    def search_and_download(
        self,
        query: str,
        duration_needed: float,
        quality: str = "hd",
    ) -> Optional[Path]:
        """
        Search Pexels and download best matching video.

        Checks cache first. If not cached, searches Pexels, finds best match,
        downloads, and caches for future use.

        Args:
            query: Search term (e.g., "office workspace")
            duration_needed: Required clip length in seconds
            quality: Video quality - "sd" (640×360), "hd" (1280×720), "uhd" (1920×1080+)

        Returns:
            Path to downloaded video, or None if failed
        """
        # Check cache first
        cached_path = self._cache_lookup(query)
        if cached_path:
            logger.debug(f"Cache hit for '{query}': {cached_path.name}")
            return cached_path

        # Not in cache - search Pexels
        logger.debug(f"Cache miss for '{query}' - searching Pexels")

        try:
            # Check rate limit before API call
            self._rate_limit_check()

            # Search for videos
            results = self._search_videos(query, per_page=5)

            if not results or not results.get('videos'):
                logger.warning(f"No Pexels results for '{query}'")
                return None

            # Find best matching video
            best_video = self._find_best_match(results['videos'], duration_needed, quality)

            if not best_video:
                logger.warning(f"No suitable video found for '{query}'")
                return None

            # Download video
            download_url = best_video['link']
            output_path = self._get_cache_path(query)

            logger.debug(f"Downloading from {download_url}")
            self._download_file(download_url, output_path)

            # Save cache metadata
            self._save_cache_metadata(query, best_video, output_path)

            return output_path

        except PexelsAPIError as e:
            logger.error(f"Pexels API error for '{query}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading '{query}': {e}")
            return None

    def _parse_csv(self, csv_path: Path) -> List[Dict[str, Any]]:
        """
        Parse B-roll plan CSV.

        Args:
            csv_path: Path to CSV file

        Returns:
            List of clip dicts

        Raises:
            FileNotFoundError: If CSV not found
            ValueError: If CSV has invalid format
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"B-roll plan CSV not found: {csv_path}")

        clips = []
        required_cols = ['start_sec', 'end_sec', 'type', 'search_query']

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Validate headers
            if not all(col in reader.fieldnames for col in required_cols):
                raise ValueError(
                    f"CSV missing required columns. "
                    f"Required: {required_cols}, Got: {reader.fieldnames}"
                )

            for i, row in enumerate(reader, 1):
                try:
                    clip = {
                        "start_time": float(row['start_sec']),
                        "end_time": float(row['end_sec']),
                        "type": row['type'].strip().lower(),
                        "search_query": row['search_query'].strip(),
                        "fade_in": float(row.get('fade_in', 0.5)),
                        "fade_out": float(row.get('fade_out', 0.5)),
                    }

                    # Validate type
                    if clip["type"] not in ['pip', 'fullframe']:
                        raise ValueError(f"Invalid type: {clip['type']} (must be 'pip' or 'fullframe')")

                    # Validate timing
                    if clip["end_time"] <= clip["start_time"]:
                        raise ValueError(f"end_sec must be > start_sec")

                    clips.append(clip)

                except (ValueError, KeyError) as e:
                    raise ValueError(f"Invalid CSV row {i}: {e}")

        return clips

    def _search_videos(self, query: str, per_page: int = 5) -> Dict[str, Any]:
        """
        Search Pexels API for videos.

        Args:
            query: Search term
            per_page: Number of results (max 80)

        Returns:
            API response dict

        Raises:
            PexelsAPIError: If API request fails
        """
        url = f"{self.BASE_URL}/search"
        headers = {"Authorization": self.api_key}
        params = {
            "query": query,
            "per_page": min(per_page, 80),
            "orientation": "landscape",  # Landscape for 16:9 videos
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)

        # Track request for rate limiting
        self._track_request()

        if response.status_code == 429:
            raise PexelsAPIError("Rate limit exceeded (429)")
        elif response.status_code != 200:
            raise PexelsAPIError(f"API error {response.status_code}: {response.text}")

        return response.json()

    def _find_best_match(
        self,
        videos: List[Dict],
        duration_needed: float,
        quality: str,
    ) -> Optional[Dict]:
        """
        Find best matching video from search results.

        Prioritizes:
        1. Videos longer than duration_needed
        2. Requested quality (hd preferred for 1280×720 composition)
        3. Higher resolution as fallback

        Args:
            videos: List of video dicts from Pexels API
            duration_needed: Minimum duration in seconds
            quality: Preferred quality ("sd", "hd", "uhd")

        Returns:
            Best matching video file dict, or None
        """
        for video in videos:
            # Check duration
            if video.get('duration', 0) < duration_needed:
                continue

            # Find video file with requested quality
            quality_file = self._find_quality_file(video.get('video_files', []), quality)

            if quality_file:
                return quality_file

        # No exact match - try any HD file
        logger.debug(f"No exact quality match, trying fallback")
        for video in videos:
            if video.get('duration', 0) < duration_needed:
                continue

            # Try HD as fallback
            hd_file = self._find_quality_file(video.get('video_files', []), "hd")
            if hd_file:
                return hd_file

        return None

    def _find_quality_file(self, video_files: List[Dict], quality: str) -> Optional[Dict]:
        """
        Find video file with specified quality.

        Args:
            video_files: List of video file dicts
            quality: Quality level ("sd", "hd", "uhd")

        Returns:
            Video file dict or None
        """
        # Quality preference mapping
        quality_widths = {
            "sd": 640,
            "hd": 1280,
            "uhd": 1920,
        }

        target_width = quality_widths.get(quality, 1280)

        # Find exact match first
        for vf in video_files:
            if vf.get('quality') == quality and vf.get('width') == target_width:
                return vf

        # Fallback: find closest match
        for vf in video_files:
            if vf.get('quality') == quality:
                return vf

        return None

    def _download_file(self, url: str, output_path: Path, retries: int = 3) -> None:
        """
        Download file from URL with retry logic.

        Args:
            url: Download URL
            output_path: Path to save file
            retries: Number of retry attempts

        Raises:
            PexelsAPIError: If download fails after retries
        """
        for attempt in range(retries):
            try:
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()

                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                logger.debug(f"Download complete: {output_path.name}")
                return

            except (requests.RequestException, IOError) as e:
                if attempt < retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Download failed (attempt {attempt + 1}/{retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise PexelsAPIError(f"Download failed after {retries} attempts: {e}")

    def _cache_lookup(self, query: str) -> Optional[Path]:
        """
        Check if video is already cached.

        Args:
            query: Search query

        Returns:
            Path to cached video or None
        """
        cache_path = self._get_cache_path(query)

        if cache_path.exists() and cache_path.stat().st_size > 0:
            # Verify it's a valid video (basic check)
            return cache_path

        return None

    def _get_cache_path(self, query: str) -> Path:
        """
        Get cache path for query.

        Uses MD5 hash of query for consistent naming.

        Args:
            query: Search query

        Returns:
            Path to cache file
        """
        # Normalize query and generate hash
        normalized = query.lower().strip()
        hash_key = hashlib.md5(normalized.encode()).hexdigest()

        return self.cache_dir / f"{hash_key}.mp4"

    def _save_cache_metadata(self, query: str, video_data: Dict, video_path: Path) -> None:
        """
        Save metadata for cached video.

        Args:
            query: Search query
            video_data: Video metadata from Pexels
            video_path: Path to cached video
        """
        metadata_path = video_path.with_suffix('.json')

        metadata = {
            "query": query,
            "download_time": time.time(),
            "video_url": video_data.get('link'),
            "quality": video_data.get('quality'),
            "width": video_data.get('width'),
            "height": video_data.get('height'),
        }

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _init_rate_limit(self) -> None:
        """Initialize rate limit tracking file."""
        if not self.rate_limit_file.exists():
            self._save_rate_limit_state({"requests": [], "last_reset": time.time()})

    def _track_request(self) -> None:
        """Track an API request for rate limiting."""
        state = self._load_rate_limit_state()
        state["requests"].append(time.time())

        # Clean old requests outside window
        cutoff = time.time() - self.RATE_WINDOW
        state["requests"] = [t for t in state["requests"] if t > cutoff]

        self._save_rate_limit_state(state)

    def _rate_limit_check(self) -> None:
        """
        Check rate limit and sleep if necessary.

        Raises:
            PexelsAPIError: If rate limit would be exceeded
        """
        state = self._load_rate_limit_state()

        # Clean old requests
        cutoff = time.time() - self.RATE_WINDOW
        recent_requests = [t for t in state["requests"] if t > cutoff]

        if len(recent_requests) >= self.RATE_LIMIT:
            # Calculate wait time until oldest request expires
            oldest = min(recent_requests)
            wait_time = (oldest + self.RATE_WINDOW) - time.time()

            if wait_time > 0:
                logger.warning(
                    f"Rate limit reached ({self.RATE_LIMIT} requests/hour). "
                    f"Waiting {wait_time:.0f}s..."
                )
                time.sleep(wait_time + 1)  # +1s buffer

    def _load_rate_limit_state(self) -> Dict:
        """Load rate limit state from file."""
        try:
            with open(self.rate_limit_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"requests": [], "last_reset": time.time()}

    def _save_rate_limit_state(self, state: Dict) -> None:
        """Save rate limit state to file."""
        with open(self.rate_limit_file, 'w') as f:
            json.dump(state, f)

    def clear_cache(self) -> None:
        """Clear all cached B-roll videos and metadata."""
        if self.cache_dir.exists():
            for file in self.cache_dir.glob("*"):
                if file.is_file():
                    file.unlink()
            logger.info(f"Cleared cache: {self.cache_dir}")
