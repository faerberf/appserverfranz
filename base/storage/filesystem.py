"""Filesystem storage implementation."""
import os
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional, List, Iterator, Tuple, Union
from .interface import StorageInterface, StorageData

class FileSystemStorage(StorageInterface):
    """Filesystem-based storage implementation."""
    
    def __init__(self, base_path: str):
        """Initialize with base storage path."""
        self.base_path = base_path
        
    def _get_node_path(self, node_type: str, node_id: str) -> str:
        """Get the full path to a node's JSON file.
        
        Args:
            node_type: Type of node (e.g. 'finance/sales_order')
            node_id: Node ID
            
        Returns:
            str: Full path to node's JSON file
        """
        # Split node type into parts and join with directory separator
        parts = [node_type]
        node_path = os.path.join(*parts)
        
        # Build full path
        full_path = os.path.join(self.base_path, node_path, f"{node_id}.json")
        
        return full_path
        
    def _ensure_dir(self, path: str) -> None:
        """Ensure directory exists."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
    def _read_versions(self, path: str) -> List[Dict[str, Any]]:
        """Read all versions from a file."""
        try:
            if not os.path.exists(path):
                return []
                
            with open(path, 'r') as f:
                data = json.load(f)
                
            # Handle legacy single version format
            if isinstance(data, dict):
                return [data]
                
            # Handle new multi-version format
            return data
            
        except Exception as e:
            print(f"Error reading versions: {str(e)}")
            return []
            
    def _to_serializable(self, data: Any) -> Any:
        """Convert data to JSON serializable format."""
        if isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, Decimal):
            return str(data)
        elif isinstance(data, dict):
            return {k: self._to_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._to_serializable(v) for v in data]
        elif isinstance(data, StorageData):
            return {
                "data": self._to_serializable(data.data),
                "version": data.version,
                "created_at": data.created_at.isoformat(),
                "updated_at": data.updated_at.isoformat()
            }
        return data
        
    def _write_versions(self, path: str, versions: List[Dict[str, Any]]) -> bool:
        """Write versions to a file."""
        try:
            # Create directory if needed
            self._ensure_dir(path)
            
            # Write data
            with open(path, 'w') as f:
                if len(versions) == 1:
                    json.dump(versions[0], f, indent=2)
                else:
                    json.dump(versions, f, indent=2)
            return True
            
        except Exception as e:
            print(f"Error writing versions: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    def write(self, node_type: str, node_id: str, data: StorageData) -> bool:
        """Write node data."""
        try:
            path = self._get_node_path(node_type, node_id)
            versions = self._read_versions(path)
            
            # Convert to serializable format
            version_data = self._to_serializable(data)
            
            # Add to versions
            versions.append(version_data)
            
            # Write back all versions
            return self._write_versions(path, versions)
            
        except Exception as e:
            print(f"Error writing node: {str(e)}")
            return False
            
    def read(self, node_type: str, node_id: str) -> Optional[StorageData]:
        """Read latest version of a node."""
        try:
            path = self._get_node_path(node_type, node_id)
            
            versions = self._read_versions(path)
            
            # Get latest version (last in list)
            if not versions:
                return None
                
            version = versions[-1]
            
            # Convert from our storage format to StorageData
            now = datetime.now(timezone.utc)
            
            if isinstance(version, dict) and "data" not in version:
                # Legacy format where the entire version is the data
                version = {"data": version}
            
            return StorageData(
                data=version.get("data", version),  # Handle both new and legacy formats
                version=version.get("version", version.get("_schema_version", 1)),
                created_at=datetime.fromisoformat(version.get("created_at", now.isoformat())),
                updated_at=datetime.fromisoformat(version.get("updated_at", now.isoformat()))
            )
            
        except Exception as e:
            print(f"  Error reading node: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def update(self, node_type: str, node_id: str, data: StorageData) -> bool:
        """Update a node by adding a new version."""
        try:
            path = self._get_node_path(node_type, node_id)
            versions = self._read_versions(path)
            if not versions:
                return False
                
            # Create new version in our storage format
            now = datetime.now(timezone.utc)
            version_data = {
                "data": self._to_serializable(data.data),
                "_schema_version": data.version,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "data_version": len(versions) + 1,
                "date_from": now.isoformat(),
                "date_to": None
            }
            
            # Add new version
            versions.append(version_data)
            
            # Write back all versions
            return self._write_versions(path, versions)
            
        except Exception as e:
            print(f"Error updating node: {str(e)}")
            return False
            
    def create(self, node_type: str, node_id: str, data: Union[Dict[str, Any], StorageData]) -> bool:
        """Create a new node."""
        try:
            # Get full path
            path = self._get_node_path(node_type, node_id)
            
            # Check if node already exists
            if os.path.exists(path):
                return False
                
            # Create directory if needed
            self._ensure_dir(path)
            
            now = datetime.now(timezone.utc)
            
            # Convert to StorageData if needed
            if isinstance(data, dict):
                # Extract schema version from data
                schema_version = data.pop("_schema_version", 1)
                if "_metadata_version" in data:
                    data.pop("_metadata_version")  # Remove if present
                
                # Create StorageData
                data = StorageData(
                    data=data,
                    version=schema_version,
                    created_at=now,
                    updated_at=now
                )
                
            # Convert to our storage format
            version_data = {
                "data": self._to_serializable(data.data),
                "_schema_version": data.version,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "data_version": 1,
                "date_from": now.isoformat(),
                "date_to": None
            }
            
            # Write initial version
            return self._write_versions(path, [version_data])
            
        except Exception:
            return False
            
    def list_nodes(self, node_type: str) -> List[str]:
        """List all nodes of a type."""
        try:
            path = os.path.join(self.base_path, node_type)
            if not os.path.exists(path):
                return []
                
            return [
                os.path.splitext(f)[0]
                for f in os.listdir(path)
                if f.endswith('.json')
            ]
            
        except Exception as e:
            print(f"Error listing nodes: {str(e)}")
            return []
            
    def get_version(self, node_type: str, node_id: str) -> Optional[int]:
        """Get schema version of a node."""
        try:
            data = self.read(node_type, node_id)
            return data.version if data else None
            
        except Exception as e:
            print(f"Error getting version: {str(e)}")
            return None
