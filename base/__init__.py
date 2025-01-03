"""Base package containing core functionality."""
from .generator import Generator
from .storage.base import Storage
from .nodes import Node

__all__ = [
    'Generator',  # Main interface for creating and managing nodes
    'Storage',    # Abstract base class for storage implementations
    'Node',       # Base class for node types
]
