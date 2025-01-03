"""Schema evolution functionality."""
import os
import json
from typing import Dict, Any, Optional, List

from .types import FieldDefinition, ValidationMode, FieldType


class SchemaVersion:
    """Represents a version of a schema."""
    
    def __init__(
        self,
        version: int,
        fields: Dict[str, FieldDefinition],
        description: str = ""
    ):
        """Initialize schema version."""
        self.version = version
        self.fields = fields
        self.description = description
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "fields": {
                name: field.to_dict() 
                for name, field in self.fields.items()
            },
            "description": self.description
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SchemaVersion":
        """Create schema version from dictionary."""
        fields = {}
        fields_data = data.get("fields", {})
        
        # Handle fields as a list (old format)
        if isinstance(fields_data, list):
            for field_data in fields_data:
                name = field_data.get("name")
                if not name:
                    continue
                    
                # Extract constraints from field data
                constraints = {}
                constraint_fields = [
                    "max_length", "min_length", "format", 
                    "allowed_values", "min_value", "max_value",
                    "field_number"
                ]
                for field in constraint_fields:
                    if field in field_data:
                        constraints[field] = field_data[field]

                field_def = FieldDefinition(
                    name=name,
                    field_type=FieldType(field_data.get("type", "string")),
                    required=field_data.get("required", False),
                    validation_mode=ValidationMode(field_data.get("validation", "none")),
                    description=field_data.get("description", ""),
                    default_value=field_data.get("default"),
                    constraints=constraints
                )
                fields[name] = field_def
                
        # Handle fields as a dict (new format)
        elif isinstance(fields_data, dict):
            for name, field_data in fields_data.items():
                # Extract constraints from field data
                constraints = {}
                constraint_fields = [
                    "max_length", "min_length", "format", 
                    "allowed_values", "min_value", "max_value",
                    "field_number"
                ]
                for field in constraint_fields:
                    if field in field_data:
                        constraints[field] = field_data[field]

                field_def = FieldDefinition(
                    name=name,
                    field_type=FieldType(field_data.get("type", "string")),
                    required=field_data.get("required", False),
                    validation_mode=ValidationMode(field_data.get("validation", "none")),
                    description=field_data.get("description", ""),
                    default_value=field_data.get("default"),
                    constraints=constraints
                )
                fields[name] = field_def
                
        return cls(
            version=data.get("version", 1),
            fields=fields,
            description=data.get("description", "")
        )


class SchemaEvolution:
    """Manages schema evolution for a node type."""
    
    def __init__(self):
        """Initialize schema evolution."""
        self.versions: Dict[int, SchemaVersion] = {}
        
    def add_version(self, version: SchemaVersion):
        """Add a schema version."""
        self.versions[version.version] = version
        
    def get_version(self, version: int) -> Optional[SchemaVersion]:
        """Get a specific schema version."""
        return self.versions.get(version)
        
    def get_latest_version(self) -> Optional[SchemaVersion]:
        """Get the latest schema version."""
        if not self.versions:
            return None
        latest_version = max(self.versions.keys())
        return self.versions[latest_version]
        
    def get_all_versions(self) -> List[SchemaVersion]:
        """Get all schema versions."""
        return list(self.versions.values())
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "versions": {
                str(version): schema.to_dict()
                for version, schema in self.versions.items()
            }
        }
        
    @classmethod
    def from_file(cls, path: str) -> "SchemaEvolution":
        """Create schema evolution from file."""
        if not os.path.exists(path):
            raise ValueError(f"Schema file not found: {path}")
            
        with open(path, "r") as f:
            data = json.load(f)
            
        # Handle new versioned metadata format
        if "versions" in data:
            versions = data["versions"]
            if isinstance(versions, dict):
                # New format where versions is a dict with version numbers as keys
                evolution = cls()
                for version_num, version_data in versions.items():
                    # Ensure version number matches
                    version_data = version_data.copy()  # Make a copy to avoid modifying original
                    version_data["version"] = int(version_num)
                    
                    # Handle fields
                    if "fields" in version_data:
                        fields = version_data["fields"]
                        # If fields is a list, convert to dict format
                        if isinstance(fields, list):
                            fields_dict = {}
                            for field in fields:
                                if "name" in field:
                                    field_name = field["name"]
                                    field_copy = field.copy()
                                    del field_copy["name"]  # Remove name from field data
                                    fields_dict[field_name] = field_copy
                            version_data["fields"] = fields_dict
                            
                    evolution.add_version(SchemaVersion.from_dict(version_data))
                return evolution
                
        # Fallback to old format
        return cls.from_dict(data)
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SchemaEvolution":
        """Create schema evolution from dictionary."""
        evolution = cls()
        
        # Handle old format where versions is a list
        versions = data.get("versions", [])
        if isinstance(versions, list):
            for version_data in versions:
                evolution.add_version(SchemaVersion.from_dict(version_data))
        
        return evolution
        
    def to_file(self, file_path: str):
        """Save to file."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
