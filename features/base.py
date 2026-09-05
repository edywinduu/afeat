from abc import ABC, abstractmethod
from pathlib import Path
from typing import Set, Dict, Any, Optional


class BaseConverter(ABC):
    """Abstract Base Class for all file converters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the converter."""
        pass

    @property
    @abstractmethod
    def supported_inputs(self) -> Set[str]:
        """Set of supported input extensions (lowercase, without leading dot)."""
        pass

    @property
    @abstractmethod
    def supported_outputs(self) -> Set[str]:
        """Set of supported output extensions (lowercase, without leading dot)."""
        pass

    def can_handle(self, source_ext: str, target_ext: str) -> bool:
        """Check if this converter can handle the requested conversion."""
        s = source_ext.lower().lstrip(".")
        t = target_ext.lower().lstrip(".")
        return s in self.supported_inputs and t in self.supported_outputs

    @abstractmethod
    def convert(
        self,
        source_path: Path,
        target_path: Path,
        quality: Optional[int] = None,
        **kwargs: Any
    ) -> bool:
        """
        Convert source_path to target_path.
        Returns True on success, False on failure.
        """
        pass
