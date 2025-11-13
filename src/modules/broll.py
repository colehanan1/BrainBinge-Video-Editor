"""
Stage 5: B-Roll Integration

Fetches B-roll footage from Pexels API based on CSV plan.

Downloads B-roll videos specified in a CSV plan file with intelligent
caching, rate limiting, and graceful degradation.

Features:
    - CSV plan parsing
    - Pexels API integration with caching
    - Rate limiting (200 requests/hour)
    - Graceful error handling (skip failed clips)

Example:
    >>> from src.modules.broll import BRollIntegrator
    >>> integrator = BRollIntegrator(config)
    >>> result = integrator.process("broll_plan.csv", "clips.json")
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, List

from src.api.pexels_client import BRollFetcher, PexelsAPIError
from src.config import Config
from src.core.processor import BaseProcessor, ProcessorResult

logger = logging.getLogger(__name__)


class BRollIntegrator(BaseProcessor):
    """
    Fetch B-roll footage from Pexels API.

    Downloads B-roll clips specified in CSV plan using Pexels API,
    with MD5-based caching and rate limiting.

    CSV Plan Format:
        start_sec,end_sec,type,search_query,fade_in,fade_out
        5.0,12.0,pip,team collaboration,0.5,0.5
        15.0,25.0,pip,office workspace,0.5,0.5

    Args:
        config: Configuration object
        temp_dir: Directory for temporary files
    """

    def __init__(self, config: Config, temp_dir: Path | None = None):
        super().__init__(config, temp_dir)

        # Get Pexels API key from environment
        self.api_key = os.getenv("PEXELS_API_KEY")
        if not self.api_key:
            logger.warning("PEXELS_API_KEY not set - B-roll integration will fail")

        # Initialize Pexels fetcher
        cache_dir = (temp_dir or Path("data/temp")) / "broll_cache"
        self.fetcher = BRollFetcher(
            api_key=self.api_key,
            cache_dir=cache_dir
        ) if self.api_key else None

    def process(
        self,
        input_path: Path,
        output_path: Path,
        script_data: Any = None,
        **kwargs: Any,
    ) -> ProcessorResult:
        """
        Download B-roll clips from CSV plan.

        Args:
            input_path: Path to B-roll plan CSV
            output_path: Path for output JSON (downloaded clips metadata)
            script_data: Not used
            **kwargs: Additional parameters

        Returns:
            ProcessorResult with downloaded clips and metadata

        Raises:
            ProcessingError: If API key missing or CSV parsing fails
        """
        start_time = time.time()

        try:
            # Validate API key
            if not self.fetcher:
                return ProcessorResult(
                    success=False,
                    output_path=None,
                    metadata={
                        "error": "PEXELS_API_KEY not configured",
                        "clip_count": 0,
                        "downloaded_count": 0,
                    }
                )

            # Download clips from plan
            logger.info(f"Fetching B-roll from plan: {input_path}")
            downloaded_clips = self.fetcher.fetch_from_plan(input_path)

            # Calculate success rate
            csv_clips = self.fetcher._parse_csv(input_path)
            total_clips = len(csv_clips)
            downloaded_count = len(downloaded_clips)
            success_rate = (downloaded_count / total_clips * 100) if total_clips > 0 else 0

            # Save output JSON
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_data = {
                "clips": [
                    {
                        "start_time": clip["start_time"],
                        "end_time": clip["end_time"],
                        "type": clip["type"],
                        "search_query": clip["search_query"],
                        "path": str(clip["path"]),
                        "fade_in": clip["fade_in"],
                        "fade_out": clip["fade_out"],
                    }
                    for clip in downloaded_clips
                ],
                "metadata": {
                    "total_requested": total_clips,
                    "successfully_downloaded": downloaded_count,
                    "success_rate": f"{success_rate:.1f}%",
                }
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2)

            processing_time = time.time() - start_time

            # Build metadata
            metadata = {
                "clip_count": total_clips,
                "downloaded_count": downloaded_count,
                "success_rate": success_rate,
                "failed_count": total_clips - downloaded_count,
                "processing_time": processing_time,
                "cache_hits": sum(1 for clip in downloaded_clips
                                if self.fetcher._cache_lookup(clip["search_query"])),
            }

            # Consider success if at least 50% downloaded
            success = success_rate >= 50.0

            return ProcessorResult(
                success=success,
                output_path=output_path,
                metadata=metadata
            )

        except FileNotFoundError as e:
            logger.error(f"B-roll plan file not found: {e}")
            return ProcessorResult(
                success=False,
                output_path=None,
                metadata={
                    "error": str(e),
                    "processing_time": time.time() - start_time,
                }
            )
        except Exception as e:
            logger.error(f"B-roll integration failed: {e}", exc_info=True)
            return ProcessorResult(
                success=False,
                output_path=None,
                metadata={
                    "error": str(e),
                    "processing_time": time.time() - start_time,
                }
            )

    def validate(self, input_path: Path, **kwargs: Any) -> List[str]:
        """
        Validate CSV plan and API access.

        Args:
            input_path: Path to B-roll plan CSV

        Returns:
            List of validation errors
        """
        errors = []

        # Check API key
        if not self.api_key:
            errors.append("PEXELS_API_KEY environment variable not set")

        # Check CSV file exists
        if not input_path.exists():
            errors.append(f"B-roll plan CSV not found: {input_path}")
        elif input_path.stat().st_size == 0:
            errors.append(f"B-roll plan CSV is empty: {input_path}")
        else:
            # Validate CSV format
            try:
                if self.fetcher:
                    self.fetcher._parse_csv(input_path)
            except Exception as e:
                errors.append(f"Invalid CSV format: {e}")

        return errors

    def estimate_duration(self, input_path: Path, **kwargs: Any) -> float:
        """
        Estimate B-roll processing duration.

        Args:
            input_path: Path to B-roll plan CSV

        Returns:
            Estimated time in seconds (depends on cache hits and API speed)
        """
        try:
            if not self.fetcher or not input_path.exists():
                return 0.0

            # Parse CSV to count clips
            clips = self.fetcher._parse_csv(input_path)
            total_clips = len(clips)

            # Estimate based on cache hits
            cached_clips = sum(1 for clip in clips
                             if self.fetcher._cache_lookup(clip["search_query"]))
            uncached_clips = total_clips - cached_clips

            # Cached: instant, Uncached: ~5s per clip (API search + download)
            estimated_time = (cached_clips * 0.1) + (uncached_clips * 5.0)

            return estimated_time

        except Exception:
            # Fallback estimate: 5s per clip
            return 30.0
