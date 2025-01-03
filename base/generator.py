"""Generator for managing data and metadata."""
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from .storage.filesystem import FileSystemStorage
from .storage.interface import StorageData
from .metadata.api import MetadataAPI
from .api.version import APIVersionManager
from .schema.evolution import SchemaEvolution, SchemaVersion
from .schema.types import FieldDefinition, FieldType, ValidationMode
from .validation import validate_data
from .counter import Counter


class Generator:
    """Generator for managing data and metadata."""
    
    def __init__(self, data_path: str, metadata_path: str, schema_evolution: Optional[SchemaEvolution] = None):
        """Initialize with paths and optional schema evolution."""
        self.data_path = data_path
        self.metadata_path = metadata_path
        self.storage = FileSystemStorage(data_path)
        self.version_manager = APIVersionManager(metadata_path)
        self.schema_evolution = schema_evolution or SchemaEvolution(metadata_path)
        
        # Initialize metadata API
        self.metadata_api = MetadataAPI(metadata_path)
        
        # Initialize counter
        self.counter = Counter(self.storage)
        
        # Load schema evolution
        if schema_evolution:
            self._load_schema_evolution(schema_evolution)
        else:
            self._load_default_schema()

    def _load_schema_evolution(self, schema_evolution: SchemaEvolution):
        """Load schema evolution from provided SchemaEvolution object."""
        try:
            # Get node type from metadata directory structure
            for root, _, files in os.walk(self.metadata_api.metadata_dir):
                for file in files:
                    if not file.endswith('.json'):
                        continue
                        
                    # Get node type from file path
                    rel_path = os.path.relpath(os.path.join(root, file), self.metadata_api.metadata_dir)
                    node_type = os.path.splitext(rel_path)[0].replace(os.path.sep, '/')
                    
                    try:
                        # Load schema evolution for this file
                        schema_file = os.path.join(root, file)
                        node_schema = SchemaEvolution.from_file(schema_file)
                        
                        # Register with version manager
                        self.version_manager.register_node_type(node_type, node_schema)
                    except Exception as e:
                        print(f"Error loading schema for {node_type}: {str(e)}")
                    
        except Exception as e:
            print(f"Error loading schema evolution: {str(e)}")

    def _load_default_schema(self):
        """Load default schema from metadata directory."""
        try:
            # Walk through metadata directory to find all JSON files
            for root, _, files in os.walk(self.metadata_api.metadata_dir):
                for file in files:
                    if not file.endswith('.json'):
                        continue
                        
                    # Get node type from file path
                    rel_path = os.path.relpath(os.path.join(root, file), self.metadata_api.metadata_dir)
                    node_type = os.path.splitext(rel_path)[0].replace(os.path.sep, '/')
                    
                    try:
                        # Load schema evolution for this file
                        schema_file = os.path.join(root, file)
                        node_schema = SchemaEvolution.from_file(schema_file)
                        
                        # Register with version manager
                        self.version_manager.register_node_type(node_type, node_schema)
                    except Exception as e:
                        print(f"Error loading schema for {node_type}: {str(e)}")
                    
        except Exception as e:
            print(f"Error loading default schema: {str(e)}")

    def _get_full_node_type(self, node_type: str) -> str:
        """Get full node type path including parent directory."""
        # Convert dots to slashes for metadata lookup
        node_type = node_type.replace('.', '/')
        
        # If node_type already includes a directory prefix (e.g., 'finance/sales_order_header'),
        # use it as is without adding the parent directory name
        if '/' in node_type:
            return node_type
            
        # Otherwise, prefix with parent directory name
        parent_dir = os.path.basename(self.data_path)
        if parent_dir:
            return f"{parent_dir}/{node_type}"
        return node_type

    def _convert_schema_dict_to_version(self, schema_dict: Dict[str, Any]) -> SchemaVersion:
        """Convert schema dictionary to SchemaVersion object."""
        fields = {}
        for field_name, field_def in schema_dict.get("fields", {}).items():
            # Handle both dict and list formats
            if isinstance(field_def, dict):
                field_data = field_def
            else:
                field_data = {
                    "name": field_name,
                    "type": field_def.get("type", "string"),
                    "required": field_def.get("required", False),
                    "validation": field_def.get("validation", "none"),
                    "default": field_def.get("default"),
                    "description": field_def.get("description", "")
                }
            
            fields[field_name] = FieldDefinition(
                name=field_name,
                field_type=FieldType(field_data.get("type", "string")),
                required=field_data.get("required", False),
                validation_mode=ValidationMode(field_data.get("validation", "none")),
                default_value=field_data.get("default"),
                description=field_data.get("description", "")
            )
            
        return SchemaVersion(
            version=schema_dict.get("version", 1),
            fields=fields,
            description=schema_dict.get("description", "")
        )

    def get_schema_version(self, node_type: str) -> Optional[int]:
        """Get latest schema version for a node type."""
        return self.version_manager.get_latest_version(node_type)

    def _validate_data(self, node_type: str, data: Dict[str, Any]) -> bool:
        """Validate data against metadata schema."""
        try:
            # Get metadata
            metadata = self.metadata_api.get_metadata(node_type)
            if not metadata:
                raise ValueError(f"No metadata found for node type {node_type}")
                
            # Get current version fields
            current_version = metadata.get("_schema_version", 1)
            version_data = next(
                (v for v in metadata["versions"].values() if v["version"] == current_version),
                None
            )
            if not version_data:
                raise ValueError(f"Version {current_version} not found in metadata")
                
            # Check required fields
            for field_name, field_def in version_data["fields"].items():
                if field_def.get("required", False) and field_name not in data:
                    raise ValueError(f"Required field {field_name} missing")
                    
            return True
            
        except Exception as e:
            raise ValueError(f"Failed to validate data: {str(e)}")

    def _get_upgrade_strategy(self, from_version: int, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get the upgrade strategy for a specific version.
        
        Args:
            from_version: Version to upgrade from
            metadata: Metadata containing upgrade definitions
            
        Returns:
            Optional[Dict[str, Any]]: Upgrade strategy if found, None otherwise
        """
        upgrade_defs = metadata.get("versions", [])
        for version_def in upgrade_defs:
            if version_def.get("version") == from_version + 1:
                return version_def.get("upgrade_definitions", {}).get(f"from_{from_version}", {})
        return None
            
    def _check_and_upgrade_data(self, node_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if data needs to be upgraded to match current metadata version."""
        try:
            # Get metadata
            metadata = self.metadata_api.get_metadata(node_type)
            if not metadata:
                raise ValueError(f"No metadata found for node type {node_type}")
                
            # Get current metadata version
            current_version = metadata.get("_schema_version", 1)
            
            # Get data version
            data_version = data.get("_schema_version", 1)
            
            # Upgrade if needed
            if data_version < current_version:
                return self._upgrade_node(node_type, data, data_version, current_version, metadata)
                
            return data
            
        except Exception as e:
            raise ValueError(f"Failed to check/upgrade data: {str(e)}")
            
    def _upgrade_node(self, node_type: str, data: Dict[str, Any], current_version: int, target_version: int, 
                     upgrade_definitions: Dict[str, Any]) -> Dict[str, Any]:
        """Upgrade node data to target version."""
        if current_version >= target_version:
            return data

        # Get upgrade path from current to target
        upgraded_data = data.copy()
        
        # Upgrade through each version sequentially
        for version in range(current_version, target_version):
            from_key = f"from_{version}"
            if from_key not in upgrade_definitions:
                continue

            upgrade_def = upgrade_definitions[from_key]
            
            # Add new fields with default values
            for field, field_type in upgrade_def.get("add_fields", {}).items():
                if field not in upgraded_data:
                    upgraded_data[field] = "" if field_type == "TEXT" else 0
            
            # Transform existing fields
            for field, transform in upgrade_def.get("transform_fields", {}).items():
                if field in upgraded_data:
                    # Handle type transformations
                    if transform.get("type") == "DECIMAL":
                        upgraded_data[field] = str(upgraded_data[field])
                    elif transform.get("type") == "FLOAT":
                        upgraded_data[field] = float(upgraded_data[field])
                    elif transform.get("type") == "INTEGER":
                        upgraded_data[field] = int(upgraded_data[field])
                    elif transform.get("type") == "TEXT":
                        upgraded_data[field] = str(upgraded_data[field])

        # Always set the metadata version to target version
        upgraded_data["_schema_version"] = target_version
        return upgraded_data

    def create_node(self, node_type: str, node_id: str, data: Dict[str, Any]) -> str:
        """Create a new node."""
        try:
            print(f"Creating node {node_type}/{node_id}")
            print(f"Data: {data}")
            
            # Get full node type path
            full_node_type = self._get_full_node_type(node_type)
            print(f"Full node type: {full_node_type}")
            
            # Check and upgrade data if needed
            data = self._check_and_upgrade_data(full_node_type, data)
            print(f"After upgrade: {data}")
            
            # Convert non-JSON-serializable values to strings
            data_copy = {}
            for key, value in data.items():
                if isinstance(value, (datetime, FieldType, ValidationMode)):
                    data_copy[key] = str(value)
                else:
                    data_copy[key] = value
                    
            print(f"After conversion: {data_copy}")
            
            # Create node with data
            if not self.storage.create(full_node_type, node_id, data_copy):
                raise ValueError(f"Failed to create node {full_node_type}/{node_id}")
                
            return node_id
            
        except Exception as e:
            print(f"Error creating node: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    def read_node(self, node_type: str, node_id: str) -> Optional[Dict[str, Any]]:
        """Read a node by ID."""
        try:
            # Read raw data
            storage_data = self.storage.read(node_type, node_id)
            if not storage_data:
                return None
                
            return storage_data.data
            
        except Exception as e:
            print(f"Error reading node: {str(e)}")
            return None

    def update_node(self, node_type: str, node_id: str, data: Dict[str, Any]) -> bool:
        """Update an existing node."""
        try:
            # Get full node type path
            full_node_type = self._get_full_node_type(node_type)
            
            # Check and upgrade data if needed
            data = self._check_and_upgrade_data(full_node_type, data)
            
            if not self._validate_data(full_node_type, data):
                raise ValueError(f"Invalid data for node type {full_node_type}")
                
            metadata = self.metadata_api.get_metadata(full_node_type)
            current_version = metadata.get("_schema_version", 1)
            data["_schema_version"] = current_version
            
            # Create storage data
            now = datetime.now(timezone.utc)
            storage_data = StorageData(
                data=data,
                version=current_version,
                created_at=now,
                updated_at=now
            )
            
            # Update node
            if not self.storage.update(full_node_type, node_id, storage_data):
                raise ValueError(f"Failed to update node {full_node_type}/{node_id}")
                
            return True
            
        except Exception as e:
            print(f"Error updating node: {str(e)}")
            return False

    def delete_node(self, node_type: str, node_id: str) -> bool:
        """Delete a node."""
        return self.storage.delete(node_type, node_id)

    def query_nodes(self, node_type: str, **kwargs) -> List[Dict[str, Any]]:
        """Query nodes by field values."""
        try:
            # Get full node type path
            full_node_type = self._get_full_node_type(node_type)
            
            # List all nodes of the type
            node_ids = self.storage.list_nodes(full_node_type)
            results = []
            
            # Read each node and check if it matches the query
            for node_id in node_ids:
                node_data = self.read_node(full_node_type, node_id)
                if not node_data:
                    continue
                    
                # Check if all query parameters match
                matches = True
                for key, value in kwargs.items():
                    if key not in node_data or node_data[key] != value:
                        matches = False
                        break
                        
                if matches:
                    results.append(node_data)
                    
            return results
            
        except Exception as e:
            print(f"Error querying nodes: {str(e)}")
            return []

    def upgrade_all_nodes(self):
        """Upgrade all nodes to latest version."""
        print("Starting system-wide node upgrade...")
        
        # Get all node types
        for node_type in self.storage.list_node_types():
            # Load metadata for node type
            try:
                metadata = self.metadata_api.get_metadata(node_type)
            except Exception as e:
                print(f"Error loading metadata: {str(e)}")
                continue
                
            if not metadata:
                print(f"No metadata found for {node_type}, skipping...")
                continue
                
            target_version = metadata.get("version", 1)
            upgrade_defs = metadata.get("upgrades", [])
            
            print(f"Processing {node_type} nodes...")
            
            # Iterate through all nodes of this type
            for node_id in self.storage.list_nodes(node_type):
                try:
                    # Read node data
                    node_data = self.storage.read(node_type, node_id)
                    if not node_data:
                        continue
                        
                    data = node_data.data
                    current_version = node_data.version
                    
                    if current_version < target_version:
                        print(f"Upgrading {node_type}/{node_id} from v{current_version} to v{target_version}")
                        
                        # Upgrade node data
                        upgraded_data = self._upgrade_node(
                            node_type, data, current_version, 
                            target_version, upgrade_defs
                        )
                        
                        if upgraded_data:
                            # Update node with upgraded data
                            self.storage.update(
                                node_type,
                                node_id,
                                StorageData(
                                    data=upgraded_data,
                                    version=target_version,
                                    created_at=node_data.created_at,
                                    updated_at=datetime.now(timezone.utc),
                                    metadata=node_data.metadata
                                )
                            )
                        
                except Exception as e:
                    print(f"Error upgrading {node_type}/{node_id}: {str(e)}")
                    continue
