"""A module to store marznode data"""

from .base import BaseStorage
from .memory import MemoryStorage

__all__ = ["BaseStorage", "MemoryStorage"]
