from pathlib import Path
from typing import List, Optional, Set, Dict
from .base import BaseConverter


class ConverterRegistry:
    """Registry and dispatcher for all file converters."""

    def __init__(self):
        self._converters: List[BaseConverter] = []

    def register(self, converter: BaseConverter) -> None:
        """Register a converter instance."""
        if converter not in self._converters:
            self._converters.append(converter)

    def get_converter(self, source_ext: str, target_ext: str) -> Optional[BaseConverter]:
        """Find the converter that can handle source_ext to target_ext."""
        s = source_ext.lower().lstrip(".")
        t = target_ext.lower().lstrip(".")
        for conv in self._converters:
            if conv.can_handle(s, t):
                return conv
        return None

    def get_compatible_sources_for_target(self, target_ext: str) -> Set[str]:
        """Get all source extensions that can be converted to target_ext."""
        t = target_ext.lower().lstrip(".")
        sources: Set[str] = set()
        for conv in self._converters:
            if t in conv.supported_outputs:
                sources.update(conv.supported_inputs)
        return sources

    def get_compatible_targets_for_source(self, source_ext: str) -> Set[str]:
        """Get all target extensions that source_ext can be converted to."""
        s = source_ext.lower().lstrip(".")
        targets: Set[str] = set()
        for conv in self._converters:
            if s in conv.supported_inputs:
                targets.update(conv.supported_outputs)
        return targets

    def list_supported_summary(self) -> Dict[str, Dict[str, Set[str]]]:
        """Returns a summary of supported converters and their formats."""
        summary = {}
        for conv in self._converters:
            summary[conv.name] = {
                "inputs": conv.supported_inputs,
                "outputs": conv.supported_outputs,
            }
        return summary


default_registry = ConverterRegistry()
