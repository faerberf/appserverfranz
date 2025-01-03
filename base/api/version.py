"""API version management."""
from typing import Dict, Any, Optional, List, Type
from datetime import datetime, timezone
import os
import json

from ..schema.evolution import SchemaVersion, SchemaEvolution
from ..schema.types import FieldDefinition, FieldType, ValidationMode
from ..validation import Validator, ValidationError
from ..storage.interface import StorageData


class APIVersion:
    """Represents an API version with schema mapping."""
    
    def __init__(
        self,
        version: str,
        schema_version: int,
        valid_from: datetime,
        valid_to: Optional[datetime] = None
    ):
        """Initialize API version.
        
        Args:
            version: API version string (e.g., "v1")
            schema_version: Schema version number
            valid_from: When this API version becomes valid
            valid_to: When this API version becomes invalid
        """
        self.version = version
        self.schema_version = schema_version
        self.valid_from = valid_from
        self.valid_to = valid_to


class APIVersionManager:
    """Manages API versions and schema evolution."""
    
    def __init__(self, metadata_path: str = None):
        """Initialize version manager.
        
        Args:
            metadata_path: Optional path to metadata directory
        """
        self.metadata_path = metadata_path
        self.node_types: Dict[str, SchemaEvolution] = {}
        
    def register_node_type(self, node_type: str, evolution: SchemaEvolution):
        """Register a node type with its schema evolution."""
        self.node_types[node_type] = evolution
        
    def get_version(self, node_type: str, version: int) -> Optional[Dict[str, Any]]:
        """Get schema version for a node type.
        
        Args:
            node_type: Type of node
            version: Schema version number
            
        Returns:
            Optional[Dict[str, Any]]: Schema version as dictionary if found
        """
        if node_type not in self.node_types:
            return None
        schema_version = self.node_types[node_type].get_version(version)
        return schema_version.to_dict() if schema_version else None
        
    def get_latest_version(self, node_type: str) -> Optional[Dict[str, Any]]:
        """Get latest schema version for a node type.
        
        Args:
            node_type: Type of node
            
        Returns:
            Optional[Dict[str, Any]]: Latest schema version as dictionary if found
        """
        if node_type not in self.node_types:
            return None
        schema_version = self.node_types[node_type].get_latest_version()
        return schema_version.to_dict() if schema_version else None
        
    def get_schema_version(self, node_type: str, version: Optional[int] = None) -> Optional[SchemaVersion]:
        """Get schema version for a node type."""
        if node_type not in self.node_types:
            return None
            
        if version is None:
            return self.node_types[node_type].get_latest_version()
            
        return self.node_types[node_type].get_version(version)
        
    def convert_data(
        self,
        node_type: str,
        data: Dict[str, Any],
        from_version: int,
        to_version: int
    ) -> Optional[Dict[str, Any]]:
        """Convert data from one version to another."""
        if node_type not in self.node_types:
            return None
            
        # Get source and target schemas
        source_schema = self.get_schema_version(node_type, from_version)
        target_schema = self.get_schema_version(node_type, to_version)
        if not source_schema or not target_schema:
            return None
            
        # Create new data with required fields
        new_data = {}
        
        # Copy existing fields that exist in new schema
        for field_name, field in target_schema.fields.items():
            if field_name in data:
                new_data[field_name] = data[field_name]
                
        # Update schema version
        new_data["_schema_version"] = to_version
        
        return new_data

    def convert_response(
        self,
        api_version: str,
        node_type: str,
        data: Dict[str, Any],
        from_version: int
    ) -> Optional[Dict[str, Any]]:
        """Convert response data to match API version."""
        try:
            # Get schema version for API version
            schema_version = self.get_schema_version(node_type)
            if not schema_version:
                return None
                
            # Create storage data
            storage_data = StorageData(
                data=data,
                version=from_version,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Convert data if needed
            if from_version != schema_version.version:
                converted_data = self.convert_data(
                    node_type,
                    storage_data.data,
                    from_version,
                    schema_version.version
                )
                if not converted_data:
                    return None
                    
                storage_data = StorageData(
                    data=converted_data,
                    version=schema_version.version,
                    created_at=storage_data.created_at,
                    updated_at=datetime.now(timezone.utc)
                )
                
            return storage_data.data
            
        except Exception as e:
            print(f"Error converting response: {str(e)}")
            return None
