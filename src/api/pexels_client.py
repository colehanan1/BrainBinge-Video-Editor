"""
Pexels API Client

Client for searching and downloading B-roll footage from Pexels.

API Documentation: https://www.pexels.com/api/documentation/

Example:
    >>> from src.api.pexels_client import PexelsClient
    >>> client = PexelsClient(api_key="your_key")
    >>> videos = client.search_videos("technology", per_page=5)
    >>> client.download_video(videos[0], "output/broll_1.mp4")
"""

from pathlib import Path
from typing import Any, Dict, List, Optional


class PexelsClient:
    """
    Client for Pexels API video search and download.

    Args:
        api_key: Pexels API key
        cache_dir: Directory for caching downloaded videos

    Example:
        >>> client = PexelsClient("api_key_here")
        >>> results = client.search_videos("ocean waves")
        >>> print(f"Found {len(results)} videos")
    """

    def __init__(self, api_key: str, cache_dir: Optional[Path] = None):
        """
        Initialize Pexels client.

        Args:
            api_key: Pexels API key from https://www.pexels.com/api/
            cache_dir: Directory for caching downloads
        """
        self.api_key = api_key
        self.cache_dir = cache_dir or Path("data/temp/broll_cache")
        self.base_url = "https://api.pexels.com/videos"

    def search_videos(
        self,
        query: str,
        per_page: int = 15,
        orientation: str = "portrait",
    ) -> List[Dict[str, Any]]:
        """
        Search for videos by keyword.

        Args:
            query: Search query (e.g., "technology", "nature")
            per_page: Number of results to return (max 80)
            orientation: Video orientation ("portrait", "landscape", "square")

        Returns:
            List of video metadata dictionaries

        Raises:
            APIError: If API request fails
        """
        # TODO: Build API request
        # TODO: Add authorization header
        # TODO: Handle pagination
        # TODO: Parse response
        # TODO: Filter by orientation and quality
        raise NotImplementedError("Pexels search not yet implemented")

    def download_video(
        self,
        video_data: Dict[str, Any],
        output_path: Path,
        quality: str = "hd",
    ) -> Path:
        """
        Download video file.

        Args:
            video_data: Video metadata from search results
            output_path: Output file path
            quality: Video quality ("sd", "hd", "uhd")

        Returns:
            Path to downloaded video file

        Raises:
            DownloadError: If download fails
        """
        # TODO: Get video URL for specified quality
        # TODO: Download video file
        # TODO: Save to output path
        # TODO: Verify download completed
        raise NotImplementedError("Video download not yet implemented")

    def get_cached_video(self, video_id: str) -> Optional[Path]:
        """
        Check if video is already cached.

        Args:
            video_id: Pexels video ID

        Returns:
            Path to cached video or None if not cached
        """
        # TODO: Check cache directory for video
        # TODO: Return path if exists
        return None

    def clear_cache(self) -> None:
        """Clear all cached B-roll videos."""
        # TODO: Remove all files from cache directory
        pass
