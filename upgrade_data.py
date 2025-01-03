#!/usr/bin/env python
"""Script to upgrade data to latest schema versions."""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from base.storage.filesystem import FileSystemStorage
from base.storage.interface import StorageData
from base.schema.evolution import SchemaEvolution, SchemaVersion, FieldDefinition, FieldType, ValidationMode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UpgradeManager:
    """Manages data upgrades."""
    
    def __init__(self, storage: FileSystemStorage, schema_dir: str):
        """Initialize upgrade manager.
        
        Args:
            storage: Storage implementation
            schema_dir: Directory containing schema files
        """
        self.storage = storage
        self.schema_dir = schema_dir
        self.evolutions: Dict[str, SchemaEvolution] = {}
        
    def load_schema(self, node_type: str) -> Optional[SchemaEvolution]:
        """Load schema evolution for a node type.
        
        Args:
            node_type: Type of node
            
        Returns:
            Optional[SchemaEvolution]: Schema evolution if found
        """
        if node_type in self.evolutions:
            return self.evolutions[node_type]
            
        # Load schema file
        schema_path = os.path.join(self.schema_dir, f"{node_type}.json")
        if not os.path.exists(schema_path):
            logger.error(f"Schema file not found: {schema_path}")
            return None
            
        try:
            with open(schema_path, 'r') as f:
                schema_data = json.load(f)
                
            evolution = SchemaEvolution()
            for version_str, version_data in schema_data.get("versions", {}).items():
                version_num = int(version_str)
                
                # Create field definitions
                fields = {}
                for field_name, field_data in version_data["fields"].items():
                    field_type = field_data["type"].upper()
                    validation = field_data.get("validation", "none").upper()
                    
                    # Extract constraints
                    constraints = {}
                    if "field_number" in field_data:
                        constraints["field_number"] = field_data["field_number"]
                    
                    fields[field_name] = FieldDefinition(
                        name=field_name,
                        field_type=getattr(FieldType, field_type),
                        required=field_data.get("required", False),
                        validation_mode=getattr(ValidationMode, validation),
                        description=field_data.get("description", ""),
                        default_value=field_data.get("default_value"),
                        constraints=constraints
                    )
                
                # Create version
                version = SchemaVersion(
                    version=version_num,
                    fields=fields,
                    description=version_data.get("description", "")
                )
                evolution.add_version(version)
                
            self.evolutions[node_type] = evolution
            return evolution
            
        except Exception as e:
            logger.error(f"Error loading schema: {str(e)}")
            return None
            
    def upgrade_node(self, node_type: str, node_id: str, verbose: bool = False) -> bool:
        """Upgrade a single node to latest version.
        
        Args:
            node_type: Type of node
            node_id: ID of node
            verbose: Enable verbose logging
            
        Returns:
            bool: True if successful
        """
        try:
            # Load schema evolution
            evolution = self.load_schema(node_type)
            if not evolution:
                return False
                
            # Get latest schema version
            latest_version = evolution.get_latest_version()
            if not latest_version:
                logger.error(f"No schema versions found for {node_type}")
                return False
                
            # Read current data
            current_data = self.storage.read(node_type, node_id)
            if not current_data:
                logger.error(f"Node not found: {node_type}/{node_id}")
                return False
                
            current_version = current_data.version
            if verbose:
                logger.info(f"Current version: {current_version}")
                logger.info(f"Latest version: {latest_version.version}")
                
            # Check if upgrade needed
            if current_version >= latest_version.version:
                if verbose:
                    logger.info(f"Node {node_type}/{node_id} already at latest version")
                return True
                
            # Upgrade through versions
            data = current_data.data
            for version in range(current_version + 1, latest_version.version + 1):
                schema_version = evolution.get_version(version)
                if not schema_version:
                    logger.error(f"Missing schema version {version}")
                    return False
                    
                if verbose:
                    logger.info(f"Upgrading to version {version}")
                    
                # Apply field changes
                new_data = {}
                for field_name, field_def in schema_version.fields.items():
                    if field_name in data:
                        new_data[field_name] = data[field_name]
                    elif field_def.required:
                        logger.error(f"Missing required field: {field_name}")
                        return False
                        
                data = new_data
                
            # Update storage with new version
            now = datetime.now(timezone.utc)
            updated_data = StorageData(
                data=data,
                version=latest_version.version,
                created_at=current_data.created_at,
                updated_at=now,
                metadata=current_data.metadata
            )
            
            success = self.storage.update(node_type, node_id, updated_data)
            if success and verbose:
                logger.info(f"Successfully upgraded {node_type}/{node_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error upgrading node: {str(e)}")
            return False
            
    def upgrade_type(self, node_type: str, verbose: bool = False) -> bool:
        """Upgrade all nodes of a type.
        
        Args:
            node_type: Type of nodes to upgrade
            verbose: Enable verbose logging
            
        Returns:
            bool: True if all successful
        """
        try:
            # List all nodes
            nodes = self.storage.list_nodes(node_type)
            if not nodes:
                logger.warning(f"No nodes found for type: {node_type}")
                return True
                
            if verbose:
                logger.info(f"Found {len(nodes)} nodes to upgrade")
                
            # Upgrade each node
            success = True
            for node_id in nodes:
                if not self.upgrade_node(node_type, node_id, verbose):
                    success = False
                    
            return success
            
        except Exception as e:
            logger.error(f"Error upgrading type: {str(e)}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Upgrade data to latest schema versions")
    parser.add_argument("node_type", help="Type of nodes to upgrade")
    parser.add_argument("--node-id", help="Specific node ID to upgrade")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    try:
        # Initialize components
        storage = FileSystemStorage("data")
        manager = UpgradeManager(storage, "metadata")
        
        # Perform upgrade
        if args.node_id:
            success = manager.upgrade_node(args.node_type, args.node_id, args.verbose)
        else:
            success = manager.upgrade_type(args.node_type, args.verbose)
            
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Upgrade failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
