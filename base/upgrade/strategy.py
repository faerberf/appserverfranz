"""Upgrade strategy definitions."""
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from ..schema.types import FieldType, ValidationMode


@dataclass
class FieldUpgradeDefinition:
    """Definition for upgrading a field."""
    
    name: str
    field_type: FieldType
    required: bool = False
    validation_mode: ValidationMode = ValidationMode.NONE
    default_value: Any = None
    description: str = ""
    transform_function: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.field_type.value,
            "required": self.required,
            "validation": self.validation_mode.value,
            "default": self.default_value,
            "description": self.description,
            "transform": self.transform_function
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FieldUpgradeDefinition':
        """Create from dictionary."""
        return cls(
            name=data["name"],
            field_type=FieldType(data["type"]),
            required=data.get("required", False),
            validation_mode=ValidationMode(data.get("validation", "none")),
            default_value=data.get("default"),
            description=data.get("description", ""),
            transform_function=data.get("transform")
        )


class UpgradeStrategy:
    """Strategy for upgrading data between schema versions."""
    
    def __init__(
        self,
        from_version: int,
        to_version: int,
        description: str = ""
    ):
        """Initialize upgrade strategy."""
        self.from_version = from_version
        self.to_version = to_version
        self.description = description
        self.add_fields: List[FieldUpgradeDefinition] = []
        self.remove_fields: List[str] = []
        self.rename_fields: Dict[str, str] = {}
        self.transform_functions: Dict[str, str] = {}
        
    def add_field(self, field_def: FieldUpgradeDefinition) -> None:
        """Add a new field."""
        self.add_fields.append(field_def)
        
    def remove_field(self, field_name: str) -> None:
        """Remove a field."""
        self.remove_fields.append(field_name)
        
    def rename_field(self, old_name: str, new_name: str) -> None:
        """Rename a field."""
        self.rename_fields[old_name] = new_name
        
    def add_transform(self, field_name: str, transform_func: str) -> None:
        """Add a transform function for a field."""
        self.transform_functions[field_name] = transform_func
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "description": self.description,
            "add_fields": [f.to_dict() for f in self.add_fields],
            "remove_fields": self.remove_fields,
            "rename_fields": self.rename_fields,
            "transform_functions": self.transform_functions
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UpgradeStrategy':
        """Create from dictionary."""
        strategy = cls(
            from_version=data["from_version"],
            to_version=data["to_version"],
            description=data.get("description", "")
        )
        
        for field_data in data.get("add_fields", []):
            strategy.add_fields.append(FieldUpgradeDefinition.from_dict(field_data))
            
        strategy.remove_fields = data.get("remove_fields", [])
        strategy.rename_fields = data.get("rename_fields", {})
        strategy.transform_functions = data.get("transform_functions", {})
        
        return strategy
