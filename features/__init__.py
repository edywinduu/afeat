"""
Features package for afeat CLI utility.
Imports all converters so they automatically register to default_registry.
"""

from .registry import default_registry, ConverterRegistry
from .base import BaseConverter
from . import img
from . import audio
from . import video
from . import doc
from .vid_downloader import SocialMediaDownloader

__all__ = [
    "default_registry",
    "ConverterRegistry",
    "BaseConverter",
    "SocialMediaDownloader",
]
