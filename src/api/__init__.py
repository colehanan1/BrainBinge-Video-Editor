"""
External API Clients

Client libraries for external services.

Modules:
    pexels_client - Pexels API client for B-roll footage
"""

from src.api.pexels_client import BRollFetcher, PexelsAPIError

__all__ = ["BRollFetcher", "PexelsAPIError"]
