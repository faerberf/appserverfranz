from abc import ABC, abstractmethod
from typing import Dict, Any
from decimal import Decimal

class UpgradeStrategy(ABC):
    @abstractmethod
    def upgrade(self, data: Dict[str, Any], fields: Dict[str, str]) -> Dict[str, Any]:
        pass

class DefaultUpgradeStrategy(UpgradeStrategy):
    def __init__(self, upgrade_def: Dict[str, Any]):
        self.add_fields = upgrade_def.get("add_fields", {})
        self.transform_fields = upgrade_def.get("transform_fields", {})

    def upgrade(self, data: Dict[str, Any], fields: Dict[str, str]) -> Dict[str, Any]:
        # Add new fields with default values
        for field, field_type in self.add_fields.items():
            if field not in data:
                data[field] = self._get_default_value(field_type)

        # Transform fields according to definitions
        for field, transform_def in self.transform_fields.items():
            if field in data:
                data[field] = self._transform_value(data[field], transform_def)

        return data

    def _get_default_value(self, field_type: str) -> Any:
        if field_type == "TEXT":
            return ""
        elif field_type == "INTEGER":
            return 0
        elif field_type == "FLOAT":
            return 0.0
        elif field_type == "DECIMAL":
            return Decimal("0.00")
        else:
            return None

    def _transform_value(self, value: Any, transform_def: Dict[str, Any]) -> Any:
        new_type = transform_def.get("type")
        if new_type == "DECIMAL":
            precision = transform_def.get("precision", 2)
            if isinstance(value, (int, float)):
                return round(Decimal(str(value)), precision)
            elif isinstance(value, str):
                return round(Decimal(value), precision)
            else:
                return Decimal("0.00")
        return value

def get_upgrade_strategy(source_version: int, target_version: Dict[str, Any]) -> UpgradeStrategy:
    """
    Get the appropriate upgrade strategy based on target version's upgrade definitions.
    
    Args:
        source_version: The version number we're upgrading from
        target_version: The target version metadata containing upgrade definitions
    
    Returns:
        An UpgradeStrategy instance that can handle the upgrade
    """
    upgrade_definitions = target_version.get("upgrade_definitions", {})
    from_key = f"from_{source_version}"
    
    if from_key not in upgrade_definitions:
        raise ValueError(f"No upgrade definition found from version {source_version}")
    
    return DefaultUpgradeStrategy(upgrade_definitions[from_key])
