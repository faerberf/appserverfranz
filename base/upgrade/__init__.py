"""Data upgrade functionality for schema evolution."""

from .manager import UpgradeManager
from .strategy import UpgradeStrategy, FieldUpgradeDefinition
from .result import UpgradeResult, UpgradeStatus

__all__ = [
    'UpgradeManager',
    'UpgradeStrategy',
    'FieldUpgradeDefinition',
    'UpgradeResult',
    'UpgradeStatus'
]
