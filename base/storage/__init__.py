"""Storage package."""
from .interface import StorageData, StorageInterface
from .filesystem import FileSystemStorage

__all__ = ["StorageData", "StorageInterface", "FileSystemStorage"]
