"""
Base Processor Interface

Abstract base class for all pipeline stage processors.
Enforces consistent interface across all processing stages.

Each stage processor must implement:
    - process(): Main processing logic
    - validate(): Input validation
    - estimate_duration(): Processing time estimation
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import Config


class ProcessorResult:
    """
    Result from a processing stage.

    Attributes:
        success: Whether the stage completed successfully
        output_path: Path to output file(s)
        metadata: Stage-specific metadata
        errors: List of error messages
        warnings: List of warning messages
    """

    def __init__(
        self,
        success: bool,
        output_path: Optional[Path] = None,
        metadata: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ):
        self.success = success
        self.output_path = output_path
        self.metadata = metadata or {}
        self.errors = errors or []
        self.warnings = warnings or []


class BaseProcessor(ABC):
    """
    Abstract base class for all processing stage implementations.

    All stage processors inherit from this class and must implement
    the abstract methods for processing, validation, and estimation.

    Args:
        config: Configuration object
        temp_dir: Directory for temporary files

    Example:
        >>> class MyProcessor(BaseProcessor):
        ...     def process(self, input_path, output_path):
        ...         # Implementation here
        ...         return ProcessorResult(success=True)
        ...     def validate(self, input_path):
        ...         return []
        ...     def estimate_duration(self, input_path):
        ...         return 10.0
    """

    def __init__(self, config: Config, temp_dir: Optional[Path] = None):
        """
        Initialize processor with configuration.

        Args:
            config: Configuration object
            temp_dir: Directory for temporary files
        """
        self.config = config
        self.temp_dir = temp_dir or Path("data/temp")
        self._cancelled = False

    @abstractmethod
    def process(
        self,
        input_path: Path,
        output_path: Path,
        **kwargs: Any,
    ) -> ProcessorResult:
        """
        Execute processing stage.

        Args:
            input_path: Path to input file
            output_path: Path for output file
            **kwargs: Additional stage-specific parameters

        Returns:
            ProcessorResult with success status and outputs

        Raises:
            ProcessingError: If processing fails
        """
        pass

    @abstractmethod
    def validate(self, input_path: Path, **kwargs: Any) -> List[str]:
        """
        Validate input before processing.

        Args:
            input_path: Path to input file
            **kwargs: Additional validation parameters

        Returns:
            List of validation error messages (empty if valid)
        """
        pass

    @abstractmethod
    def estimate_duration(self, input_path: Path, **kwargs: Any) -> float:
        """
        Estimate processing duration.

        Args:
            input_path: Path to input file
            **kwargs: Additional parameters

        Returns:
            Estimated processing time in seconds
        """
        pass

    def cancel(self) -> None:
        """
        Request cancellation of current processing.

        Sets cancellation flag that should be checked periodically
        during processing.
        """
        self._cancelled = True

    def is_cancelled(self) -> bool:
        """
        Check if cancellation has been requested.

        Returns:
            True if cancellation requested
        """
        return self._cancelled

    def reset(self) -> None:
        """Reset processor state for next operation."""
        self._cancelled = False

    def get_stage_name(self) -> str:
        """
        Get human-readable stage name.

        Returns:
            Stage name (e.g., "Audio Extraction")
        """
        return self.__class__.__name__

    def cleanup(self) -> None:
        """
        Clean up resources after processing.

        Override this method to clean up stage-specific resources
        like temporary files, connections, etc.
        """
        pass
