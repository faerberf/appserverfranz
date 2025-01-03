"""Metadata manager for handling schema and version information."""
import os
import json
from typing import Dict, Any, Optional

from ..schema.evolution import SchemaEvolution


class MetadataManager:
    """Manager for handling metadata operations."""
    
    def __init__(self, metadata_dir: str):
        """Initialize with metadata directory path."""
        self.metadata_dir = metadata_dir
        
    def load_schema_evolution(self, node_type: str) -> Optional[SchemaEvolution]:
        """Load schema evolution for a node type."""
        try:
            schema_file = os.path.join(self.metadata_dir, f"{node_type}.json")
            if not os.path.exists(schema_file):
                return None
                
            return SchemaEvolution.from_file(schema_file)
            
        except Exception as e:
            print(f"Error loading schema evolution for {node_type}: {str(e)}")
            return None
            
    def save_schema_evolution(self, node_type: str, evolution: SchemaEvolution) -> bool:
        """Save schema evolution for a node type."""
        try:
            schema_file = os.path.join(self.metadata_dir, f"{node_type}.json")
            evolution.to_file(schema_file)
            return True
            
        except Exception as e:
            print(f"Error saving schema evolution for {node_type}: {str(e)}")
            return False
            
    def load_metadata(self, node_type: str) -> Optional[Dict[str, Any]]:
        """Load metadata for a node type.
        
        Args:
            node_type: Type of node to load metadata for
            
        Returns:
            Optional[Dict[str, Any]]: Metadata if found, None otherwise
        """
        try:
            
            # Load schema evolution
            evolution = self.load_schema_evolution(node_type)
            if not evolution:
                return None
                
            # Get latest version
            latest_version = evolution.get_latest_version()
            if not latest_version:
                return None
                
            # Create metadata
            metadata = {
                "node_type": node_type,
                "version": latest_version.version,
                "_metadata_version": latest_version.version,
                "fields": latest_version.fields,
                "description": latest_version.description,
                "versions": []
            }
            # Add version definitions

            for version in evolution.get_all_versions():
                metadata["versions"].append({
                    "version": version.version,
                    "fields": version.fields,
                    "description": version.description,
                    "upgrade_definitions": {}
                })
            return metadata
            
        except Exception as e:
            print(f"Error loading metadata for {node_type}: {str(e)}")
            return None
            
    def get_schema(self, node_type: str) -> Optional[Dict[str, Any]]:
        """Get schema for a node type.
        
        Args:
            node_type: Type of node to get schema for
            
        Returns:
            Optional[Dict[str, Any]]: Schema if found, None otherwise
        """
        try:
            # Load metadata
            metadata = self.load_metadata(node_type)
            if not metadata:
                return None
                
            # Convert FieldDefinition objects back to dictionaries
            fields = {}
            for field_name, field_def in metadata["fields"].items():
                fields[field_name] = {
                    "type": field_def.field_type.value,
                    "required": field_def.required,
                    "validation": field_def.validation_mode.value,
                    "default": field_def.default_value,
                    "description": field_def.description
                }
                
            # Create schema
            schema = {
                "version": metadata["version"],
                "fields": fields,
                "description": metadata.get("description", "")
            }
            
            return schema
            
        except Exception as e:
            print(f"Error getting schema for {node_type}: {str(e)}")
            return None
