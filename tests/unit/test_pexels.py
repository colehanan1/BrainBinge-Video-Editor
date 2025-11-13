"""
Unit Tests for Pexels API Client

Tests B-roll fetching with mocked API responses.
"""

import json
import pytest
import time
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.api.pexels_client import BRollFetcher, PexelsAPIError


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create temporary cache directory."""
    cache_dir = tmp_path / "broll_cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def fetcher(temp_cache_dir):
    """Create BRollFetcher instance with temp cache."""
    return BRollFetcher(api_key="test_api_key", cache_dir=temp_cache_dir)


@pytest.fixture
def sample_csv(tmp_path):
    """Create sample B-roll plan CSV."""
    csv_content = """start_sec,end_sec,type,search_query,fade_in,fade_out
5.0,12.0,pip,team collaboration,0.5,0.5
15.0,25.0,pip,office workspace,0.5,0.5
30.0,40.0,fullframe,product demo,1.0,1.0
"""
    csv_path = tmp_path / "broll_plan.csv"
    csv_path.write_text(csv_content, encoding="utf-8")
    return csv_path


@pytest.fixture
def mock_pexels_response():
    """Mock Pexels API response."""
    return {
        "page": 1,
        "per_page": 5,
        "videos": [
            {
                "id": 123456,
                "duration": 15,
                "video_files": [
                    {
                        "id": 1,
                        "quality": "hd",
                        "width": 1280,
                        "height": 720,
                        "link": "https://example.com/video-hd.mp4"
                    },
                    {
                        "id": 2,
                        "quality": "sd",
                        "width": 640,
                        "height": 360,
                        "link": "https://example.com/video-sd.mp4"
                    }
                ]
            },
            {
                "id": 789012,
                "duration": 20,
                "video_files": [
                    {
                        "id": 3,
                        "quality": "hd",
                        "width": 1280,
                        "height": 720,
                        "link": "https://example.com/video2-hd.mp4"
                    }
                ]
            }
        ]
    }


class TestBRollFetcherInit:
    """Test BRollFetcher initialization."""

    def test_init_with_custom_cache_dir(self, temp_cache_dir):
        """Test initialization with custom cache directory."""
        fetcher = BRollFetcher(api_key="test_key", cache_dir=temp_cache_dir)

        assert fetcher.api_key == "test_key"
        assert fetcher.cache_dir == temp_cache_dir
        assert fetcher.cache_dir.exists()

    def test_init_with_default_cache_dir(self):
        """Test initialization with default cache directory."""
        fetcher = BRollFetcher(api_key="test_key")

        assert fetcher.cache_dir == Path("data/temp/broll_cache")

    def test_rate_limit_file_created(self, fetcher):
        """Test rate limit tracking file is created."""
        assert fetcher.rate_limit_file.exists()

        # Check initial state
        with open(fetcher.rate_limit_file, 'r') as f:
            state = json.load(f)

        assert "requests" in state
        assert "last_reset" in state
        assert state["requests"] == []


class TestCSVParsing:
    """Test CSV plan parsing."""

    def test_parse_valid_csv(self, fetcher, sample_csv):
        """Test parsing valid CSV file."""
        clips = fetcher._parse_csv(sample_csv)

        assert len(clips) == 3
        assert clips[0]["start_time"] == 5.0
        assert clips[0]["end_time"] == 12.0
        assert clips[0]["type"] == "pip"
        assert clips[0]["search_query"] == "team collaboration"
        assert clips[0]["fade_in"] == 0.5
        assert clips[0]["fade_out"] == 0.5

    def test_parse_csv_missing_file(self, fetcher, tmp_path):
        """Test error when CSV file doesn't exist."""
        missing_csv = tmp_path / "nonexistent.csv"

        with pytest.raises(FileNotFoundError, match="B-roll plan CSV not found"):
            fetcher._parse_csv(missing_csv)

    def test_parse_csv_missing_required_columns(self, fetcher, tmp_path):
        """Test error when CSV missing required columns."""
        csv_content = """start_sec,end_sec
5.0,12.0
"""
        csv_path = tmp_path / "invalid.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        with pytest.raises(ValueError, match="CSV missing required columns"):
            fetcher._parse_csv(csv_path)

    def test_parse_csv_invalid_type(self, fetcher, tmp_path):
        """Test error when type is not 'pip' or 'fullframe'."""
        csv_content = """start_sec,end_sec,type,search_query
5.0,12.0,invalid_type,test query
"""
        csv_path = tmp_path / "invalid_type.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        with pytest.raises(ValueError, match="Invalid type"):
            fetcher._parse_csv(csv_path)

    def test_parse_csv_invalid_timing(self, fetcher, tmp_path):
        """Test error when end_sec <= start_sec."""
        csv_content = """start_sec,end_sec,type,search_query
12.0,5.0,pip,test query
"""
        csv_path = tmp_path / "invalid_timing.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        with pytest.raises(ValueError, match="end_sec must be > start_sec"):
            fetcher._parse_csv(csv_path)

    def test_parse_csv_default_fade_values(self, fetcher, tmp_path):
        """Test default fade values when not specified."""
        csv_content = """start_sec,end_sec,type,search_query
5.0,12.0,pip,test query
"""
        csv_path = tmp_path / "no_fade.csv"
        csv_path.write_text(csv_content, encoding="utf-8")

        clips = fetcher._parse_csv(csv_path)

        assert clips[0]["fade_in"] == 0.5  # Default
        assert clips[0]["fade_out"] == 0.5  # Default


class TestCaching:
    """Test video caching functionality."""

    def test_get_cache_path_md5_hash(self, fetcher):
        """Test cache path uses MD5 hash of query."""
        path1 = fetcher._get_cache_path("team collaboration")
        path2 = fetcher._get_cache_path("team collaboration")
        path3 = fetcher._get_cache_path("different query")

        # Same query should produce same hash
        assert path1 == path2

        # Different query should produce different hash
        assert path1 != path3

        # Should be .mp4 file in cache dir
        assert path1.suffix == ".mp4"
        assert path1.parent == fetcher.cache_dir

    def test_cache_lookup_miss(self, fetcher):
        """Test cache lookup when file doesn't exist."""
        result = fetcher._cache_lookup("nonexistent query")
        assert result is None

    def test_cache_lookup_hit(self, fetcher):
        """Test cache lookup when file exists."""
        # Create cached file
        cache_path = fetcher._get_cache_path("test query")
        cache_path.write_bytes(b"fake video data")

        result = fetcher._cache_lookup("test query")
        assert result == cache_path

    def test_cache_lookup_empty_file(self, fetcher):
        """Test cache lookup rejects empty files."""
        # Create empty cached file
        cache_path = fetcher._get_cache_path("test query")
        cache_path.write_bytes(b"")

        result = fetcher._cache_lookup("test query")
        assert result is None

    def test_save_cache_metadata(self, fetcher):
        """Test saving cache metadata JSON."""
        video_data = {
            "link": "https://example.com/video.mp4",
            "quality": "hd",
            "width": 1280,
            "height": 720,
        }
        video_path = fetcher.cache_dir / "test_video.mp4"

        fetcher._save_cache_metadata("test query", video_data, video_path)

        # Check metadata file created
        metadata_path = video_path.with_suffix('.json')
        assert metadata_path.exists()

        # Check metadata content
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        assert metadata["query"] == "test query"
        assert metadata["video_url"] == "https://example.com/video.mp4"
        assert metadata["quality"] == "hd"
        assert metadata["width"] == 1280
        assert metadata["height"] == 720
        assert "download_time" in metadata


class TestPexelsAPI:
    """Test Pexels API interactions."""

    @patch('requests.get')
    def test_search_videos_success(self, mock_get, fetcher, mock_pexels_response):
        """Test successful Pexels API search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_pexels_response
        mock_get.return_value = mock_response

        result = fetcher._search_videos("test query", per_page=5)

        assert result == mock_pexels_response
        assert len(result["videos"]) == 2

        # Check API request
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://api.pexels.com/videos/search"
        assert call_args[1]["headers"]["Authorization"] == "test_api_key"
        assert call_args[1]["params"]["query"] == "test query"
        assert call_args[1]["params"]["per_page"] == 5
        assert call_args[1]["params"]["orientation"] == "landscape"

    @patch('requests.get')
    def test_search_videos_rate_limit_error(self, mock_get, fetcher):
        """Test handling of rate limit error (429)."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        with pytest.raises(PexelsAPIError, match="Rate limit exceeded"):
            fetcher._search_videos("test query")

    @patch('requests.get')
    def test_search_videos_api_error(self, mock_get, fetcher):
        """Test handling of API error (500)."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_get.return_value = mock_response

        with pytest.raises(PexelsAPIError, match="API error 500"):
            fetcher._search_videos("test query")

    def test_find_best_match_by_duration(self, fetcher, mock_pexels_response):
        """Test finding best match by duration."""
        videos = mock_pexels_response["videos"]

        # Need 10 seconds, first video (15s) should match
        result = fetcher._find_best_match(videos, duration_needed=10, quality="hd")

        assert result is not None
        assert result["quality"] == "hd"
        assert result["width"] == 1280

    def test_find_best_match_insufficient_duration(self, fetcher, mock_pexels_response):
        """Test no match when videos are too short."""
        videos = mock_pexels_response["videos"]

        # Need 30 seconds, no video is long enough
        result = fetcher._find_best_match(videos, duration_needed=30, quality="hd")

        assert result is None

    def test_find_quality_file_exact_match(self, fetcher):
        """Test finding exact quality match."""
        video_files = [
            {"quality": "sd", "width": 640},
            {"quality": "hd", "width": 1280},
            {"quality": "uhd", "width": 1920},
        ]

        result = fetcher._find_quality_file(video_files, "hd")

        assert result is not None
        assert result["quality"] == "hd"
        assert result["width"] == 1280

    def test_find_quality_file_fallback(self, fetcher):
        """Test fallback when exact width doesn't match."""
        video_files = [
            {"quality": "hd", "width": 1920},  # HD but different width
        ]

        result = fetcher._find_quality_file(video_files, "hd")

        assert result is not None
        assert result["quality"] == "hd"


class TestDownloading:
    """Test video downloading."""

    @patch('requests.get')
    def test_download_file_success(self, mock_get, fetcher):
        """Test successful file download."""
        mock_response = Mock()
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        output_path = fetcher.cache_dir / "test_video.mp4"

        fetcher._download_file("https://example.com/video.mp4", output_path)

        assert output_path.exists()
        assert output_path.read_bytes() == b"chunk1chunk2"

    @patch('requests.get')
    @patch('time.sleep')
    def test_download_file_retry(self, mock_sleep, mock_get, fetcher):
        """Test download retry on failure."""
        # First attempt fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = Exception("Connection error")

        mock_response_success = Mock()
        mock_response_success.iter_content.return_value = [b"data"]
        mock_response_success.raise_for_status = Mock()

        mock_get.side_effect = [mock_response_fail, mock_response_success]

        output_path = fetcher.cache_dir / "test_video.mp4"

        fetcher._download_file("https://example.com/video.mp4", output_path, retries=3)

        # Should have retried once
        assert mock_get.call_count == 2
        assert mock_sleep.call_count == 1
        assert output_path.exists()

    @patch('requests.get')
    @patch('time.sleep')
    def test_download_file_retry_exhausted(self, mock_sleep, mock_get, fetcher):
        """Test download fails after retries exhausted."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Connection error")
        mock_get.return_value = mock_response

        output_path = fetcher.cache_dir / "test_video.mp4"

        with pytest.raises(PexelsAPIError, match="Download failed after"):
            fetcher._download_file("https://example.com/video.mp4", output_path, retries=2)

        # Should have tried twice
        assert mock_get.call_count == 2


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_track_request(self, fetcher):
        """Test tracking API requests."""
        initial_state = fetcher._load_rate_limit_state()
        initial_count = len(initial_state["requests"])

        fetcher._track_request()

        state = fetcher._load_rate_limit_state()
        assert len(state["requests"]) == initial_count + 1

    def test_rate_limit_check_under_limit(self, fetcher):
        """Test rate limit check when under limit."""
        # Should not raise or sleep
        fetcher._rate_limit_check()

    @patch('time.sleep')
    def test_rate_limit_check_at_limit(self, mock_sleep, fetcher):
        """Test rate limit check when at limit."""
        # Simulate 200 requests in the last hour
        current_time = time.time()
        state = {
            "requests": [current_time - 100 for _ in range(200)],
            "last_reset": current_time
        }
        fetcher._save_rate_limit_state(state)

        fetcher._rate_limit_check()

        # Should sleep
        assert mock_sleep.called

    def test_rate_limit_state_cleanup(self, fetcher):
        """Test old requests are cleaned up."""
        # Add old requests (over 1 hour ago)
        old_time = time.time() - 7200  # 2 hours ago
        state = {
            "requests": [old_time, old_time, old_time],
            "last_reset": old_time
        }
        fetcher._save_rate_limit_state(state)

        fetcher._track_request()

        # Old requests should be removed
        new_state = fetcher._load_rate_limit_state()
        assert len(new_state["requests"]) == 1


class TestSearchAndDownload:
    """Test integrated search and download workflow."""

    @patch('src.api.pexels_client.BRollFetcher._download_file')
    @patch('requests.get')
    def test_search_and_download_cache_hit(self, mock_get, mock_download, fetcher):
        """Test search returns cached video."""
        # Create cached file
        cache_path = fetcher._get_cache_path("test query")
        cache_path.write_bytes(b"cached video data")

        result = fetcher.search_and_download("test query", duration_needed=10)

        # Should return cached path without API call
        assert result == cache_path
        mock_get.assert_not_called()
        mock_download.assert_not_called()

    @patch('src.api.pexels_client.BRollFetcher._download_file')
    @patch('requests.get')
    def test_search_and_download_cache_miss(self, mock_get, mock_download,
                                            fetcher, mock_pexels_response):
        """Test search downloads new video."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_pexels_response
        mock_get.return_value = mock_response

        result = fetcher.search_and_download("test query", duration_needed=10)

        # Should have called API and download
        assert mock_get.called
        assert mock_download.called
        assert result is not None

    @patch('requests.get')
    def test_search_and_download_no_results(self, mock_get, fetcher):
        """Test search with no results."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"videos": []}
        mock_get.return_value = mock_response

        result = fetcher.search_and_download("test query", duration_needed=10)

        assert result is None

    @patch('requests.get')
    def test_search_and_download_api_error(self, mock_get, fetcher):
        """Test graceful handling of API errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_get.return_value = mock_response

        result = fetcher.search_and_download("test query", duration_needed=10)

        # Should return None instead of raising
        assert result is None


class TestFetchFromPlan:
    """Test full CSV workflow."""

    @patch('src.api.pexels_client.BRollFetcher.search_and_download')
    def test_fetch_from_plan_all_success(self, mock_search, fetcher, sample_csv):
        """Test fetching all clips from CSV."""
        # Mock successful downloads
        mock_search.side_effect = [
            Path("/cache/video1.mp4"),
            Path("/cache/video2.mp4"),
            Path("/cache/video3.mp4"),
        ]

        result = fetcher.fetch_from_plan(sample_csv)

        assert len(result) == 3
        assert all("path" in clip for clip in result)
        assert result[0]["search_query"] == "team collaboration"
        assert result[1]["search_query"] == "office workspace"
        assert result[2]["search_query"] == "product demo"

    @patch('src.api.pexels_client.BRollFetcher.search_and_download')
    def test_fetch_from_plan_partial_failure(self, mock_search, fetcher, sample_csv):
        """Test graceful degradation when some downloads fail."""
        # First and third succeed, second fails
        mock_search.side_effect = [
            Path("/cache/video1.mp4"),
            None,  # Failed download
            Path("/cache/video3.mp4"),
        ]

        result = fetcher.fetch_from_plan(sample_csv)

        # Should return 2 successful clips
        assert len(result) == 2
        assert result[0]["search_query"] == "team collaboration"
        assert result[1]["search_query"] == "product demo"

    @patch('src.api.pexels_client.BRollFetcher.search_and_download')
    def test_fetch_from_plan_exception_handling(self, mock_search, fetcher, sample_csv):
        """Test exception handling during fetch."""
        # First succeeds, second raises exception, third succeeds
        mock_search.side_effect = [
            Path("/cache/video1.mp4"),
            Exception("Network error"),
            Path("/cache/video3.mp4"),
        ]

        result = fetcher.fetch_from_plan(sample_csv)

        # Should return 2 successful clips
        assert len(result) == 2


class TestClearCache:
    """Test cache clearing."""

    def test_clear_cache(self, fetcher):
        """Test clearing all cached files."""
        # Create some cached files
        (fetcher.cache_dir / "video1.mp4").write_bytes(b"data1")
        (fetcher.cache_dir / "video2.mp4").write_bytes(b"data2")
        (fetcher.cache_dir / "metadata.json").write_text("{}")

        fetcher.clear_cache()

        # All files should be deleted (except directories)
        remaining_files = list(fetcher.cache_dir.glob("*.mp4"))
        assert len(remaining_files) == 0
