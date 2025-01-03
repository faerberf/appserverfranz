import os
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# If your project references these, keep them; otherwise remove or adapt as needed:
# from ..schema.types import FieldType, ValidationMode, FieldDefinition
# from ..schema.evolution import SchemaVersion

def convert_fields_dict_to_list(fields_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert a dict of field definitions into a list (for easier UI editing).
    """
    fields_list = []
    for _, field_data in fields_dict.items():
        field_copy = field_data.copy()
        # Optional: handle "validation" vs. "validation_mode"
        if "validation" in field_copy and "validation_mode" not in field_copy:
            field_copy["validation_mode"] = field_copy.pop("validation")
        fields_list.append(field_copy)
    # Sort by field_number to keep ordering consistent
    fields_list.sort(key=lambda x: x.get("field_number", 999999))
    return fields_list

def convert_fields_list_to_dict(fields_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Convert a list of field definitions into a dict keyed by "name".
    """
    fields_dict = {}
    for f in fields_list:
        field_copy = f.copy()
        field_name = field_copy.get("name")
        if not field_name:
            continue
        # Optional: handle "validation_mode" vs. "validation"
        if "validation_mode" in field_copy and "validation" not in field_copy:
            field_copy["validation"] = field_copy.pop("validation_mode")
        fields_dict[field_name] = field_copy
    return fields_dict

class MetadataAPI:
    """
    A single merged MetadataAPI class that handles reading/writing
    node_types, metadata, versions, fields, etc.
    """

    def __init__(self, metadata_dir: str):
        """
        Args:
            metadata_dir: Base directory for metadata files.
        """
        self._metadata_dir = metadata_dir
        os.makedirs(self._metadata_dir, exist_ok=True)

    @property
    def metadata_dir(self) -> str:
        """
        Return the path to the metadata directory.
        """
        return self._metadata_dir

    def _get_metadata_path(self, node_type: str) -> str:
        """
        Compute the JSON file path for a given node_type, supporting subfolders.
        """
        # Convert dots to slashes if needed (legacy usage),
        # you can remove or adapt if you prefer strict handling.
        safe_type = node_type.replace('.', '/')
        # Also support forward slashes in node_type to allow subdirectories:
        safe_type = safe_type.replace('/', os.sep)

        # Ensure subdirectories exist, then return .json path
        full_path = os.path.join(self._metadata_dir, f"{safe_type}.json")
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        return full_path

    def _validate_node_type(self, node_type: str) -> None:
        """
        Validate node type format (basic checks).
        """
        if not node_type:
            raise ValueError("Node type cannot be empty")

        parts = node_type.split("/")
        if len(parts) > 2:
            raise ValueError("Node type can only have one '/' separator")

        if "" in parts:
            raise ValueError("Node type components cannot be empty")

    def _validate_fields(self, fields: List[Dict[str, Any]]) -> None:
        """
        Validate field definitions before creating or updating metadata.
        """
        if not fields:
            raise ValueError("Fields list cannot be empty")

        field_names = set()
        for field in fields:
            name = field.get("name")
            if not name:
                raise ValueError("Field must have a name")
            if name in field_names:
                raise ValueError(f"Duplicate field name: {name}")
            field_names.add(name)

            field_type = field.get("type")
            if not field_type:
                raise ValueError(f"Field {name} must have a type")
            # If you have an enum or a known set of types, check them here.
            # For example:
            # if field_type not in [e.value for e in FieldType]:
            #     raise ValueError(f"Invalid field type for {name}: {field_type}")

    def _convert_metadata_format(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert older metadata formats to the newer versioned format if necessary.
        """
        # If metadata is already in the new format (versions is a dict), return as is
        if isinstance(metadata.get("versions"), dict):
            return metadata

        # If versions is a list, convert to dict format
        if isinstance(metadata.get("versions"), list):
            versions_dict = {}
            versions = metadata["versions"]
            for version in versions:
                version_num = str(version.get("version", 1))
                fields = version.get("fields", [])
                if isinstance(fields, list):
                    fields_dict = {}
                    for field in fields:
                        field_name = field.get("name")
                        if field_name:
                            fields_dict[field_name] = field
                    version["fields"] = fields_dict
                versions_dict[version_num] = version
            metadata["versions"] = versions_dict
            return metadata

        # If no versions key, create a '1' with everything
        if "versions" not in metadata:
            version_1 = {
                "version": 1,
                "type": metadata.get("type", ""),
                "name": metadata.get("name", metadata.get("type", "")),
                "description": metadata.get("description", ""),
                "_schema_version": metadata.get("_schema_version", 1),
                "valid_from": datetime.now().isoformat(),
                "valid_to": None,
                "compatibility": "forward",
                "node_metadata": metadata.get("node_metadata", {
                    "upgrade_behavior": "merge_data",
                    "versioning": "enabled",
                    "archive_old_versions": True,
                    "validation_on_update": True,
                    "audit_changes": True,
                    "cascade_delete": True
                })
            }
            fields = metadata.get("fields", [])
            if isinstance(fields, list):
                fields_dict = {}
                for field in fields:
                    field_name = field.get("name")
                    if field_name:
                        fields_dict[field_name] = field
                version_1["fields"] = fields_dict
            else:
                version_1["fields"] = fields
            return {"versions": {"1": version_1}}

        return metadata

    def get_metadata(self, node_type: str) -> Optional[Dict[str, Any]]:
        """
        Load metadata from JSON, converting older formats if needed.
        """
        try:
            self._validate_node_type(node_type)
            path = self._get_metadata_path(node_type)
            if not os.path.exists(path):
                return None
            with open(path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            # Convert to new format if needed
            metadata = self._convert_metadata_format(metadata)
            # Ensure versions is a dict
            versions = metadata.get("versions", {})
            if not isinstance(versions, dict):
                versions_dict = {}
                for version in versions:
                    version_num = str(version.get("version", 1))
                    versions_dict[version_num] = version
                metadata["versions"] = versions_dict
            return metadata
        except Exception as e:
            print(f"Error reading metadata: {str(e)}")
            return None

    def create_metadata(
        self,
        node_type: str,
        fields: Union[List[Dict[str, Any]], Dict[str, Dict[str, Any]]] = None,
        description: str = "",
        _schema_version: int = 1,
        node_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create metadata for a node type (version = 1).
        """
        try:
            self._validate_node_type(node_type)
            if isinstance(fields, list):
                fields_dict = convert_fields_list_to_dict(fields)
            elif isinstance(fields, dict):
                fields_dict = fields
            else:
                fields_dict = {}

            if node_metadata is None:
                node_metadata = {
                    "upgrade_behavior": "merge_data",
                    "versioning": "enabled",
                    "archive_old_versions": True,
                    "validation_on_update": True,
                    "audit_changes": True,
                    "cascade_delete": True
                }

            path = self._get_metadata_path(node_type)
            if os.path.exists(path):
                raise ValueError(f"Metadata already exists for {node_type}")

            metadata = {
                "versions": {
                    "1": {
                        "version": 1,
                        "type": node_type,
                        "name": node_type,
                        "description": description,
                        "_schema_version": _schema_version,
                        "valid_from": datetime.now().isoformat(),
                        "valid_to": None,
                        "compatibility": "forward",
                        "node_metadata": node_metadata,
                        "fields": fields_dict
                    }
                }
            }

            with open(path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
            return True
        except Exception as e:
            print(f"Error creating metadata: {str(e)}")
            raise

    def update_metadata(
        self,
        node_type: str,
        fields: Optional[List[Dict[str, Any]]] = None,
        description: Optional[str] = None,
        _schema_version: Optional[int] = None,
        upgrade_definitions: Optional[Dict[str, Any]] = None,
        node_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update metadata for a node type by creating a new version of the schema (version = max+1),
        or updating the existing version if fields=None.
        If 'fields' is provided, it is expected to be a list; it will be converted internally to a dict.
        """
        try:
            self._validate_node_type(node_type)
            metadata = self.get_metadata(node_type)
            if not metadata:
                raise ValueError(f"No metadata found for {node_type}")

            versions = metadata.get("versions", {})
            current_version_num = max(map(int, versions.keys()))
            current_version = versions[str(current_version_num)]
            current_schema_version = current_version.get("_schema_version", 1)

            # If a new _schema_version is provided, ensure it's not a downgrade
            if _schema_version is not None and _schema_version < current_schema_version:
                raise ValueError(f"Cannot downgrade version from {current_schema_version} to {_schema_version}")

            # If fields are provided, we create a new version
            if fields is not None:
                self._validate_fields(fields)

                # Mark old version's valid_to
                current_version["valid_to"] = datetime.now().isoformat()

                new_version_num = current_version_num + 1
                new_version = {
                    "version": new_version_num,
                    "type": node_type,
                    "name": node_type,
                    "description": description or current_version.get("description", ""),
                    "_schema_version": _schema_version or current_schema_version,
                    "valid_from": datetime.now().isoformat(),
                    "valid_to": None,
                    "compatibility": "forward",
                    "node_metadata": (
                        node_metadata if node_metadata is not None
                        else current_version.get("node_metadata", {
                            "upgrade_behavior": "merge_data",
                            "versioning": "enabled",
                            "archive_old_versions": True,
                            "validation_on_update": True,
                            "audit_changes": True,
                            "cascade_delete": True
                        })
                    ),
                    # Convert the incoming list of fields into a dict before saving
                    "fields": convert_fields_list_to_dict(fields),
                    "upgrade_definitions": upgrade_definitions or {}
                }
                metadata["versions"][str(new_version_num)] = new_version

            else:
                # If fields is None, just update some metadata in the current version
                if description is not None:
                    current_version["description"] = description
                if node_metadata is not None:
                    current_version["node_metadata"] = node_metadata
                if upgrade_definitions is not None:
                    current_version["upgrade_definitions"] = upgrade_definitions
                if _schema_version is not None:
                    # ensure we are not downgrading
                    if _schema_version < current_schema_version:
                        raise ValueError(f"Cannot downgrade version from {current_schema_version} to {_schema_version}")
                    current_version["_schema_version"] = _schema_version

            # Write out changes
            path = self._get_metadata_path(node_type)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            return True
        except Exception as e:
            print(f"Error updating metadata: {str(e)}")
            raise

        
    def update_metadata(self, node_type: str, metadata: dict) -> bool:
        """
        Update metadata for a given node type.
        """
        try:
            self._validate_node_type(node_type)
            current_version = self._get_current_metadata(node_type)
            current_version.update(metadata)
            return True
        except Exception as e:
            print(f"Error updating metadata: {str(e)}")
            raise
    def delete_metadata(self, node_type: str) -> bool:
        """
        Delete metadata file for a node type.
        """
        try:
            self._validate_node_type(node_type)
            path = self._get_metadata_path(node_type)
            if os.path.exists(path):
                os.remove(path)
            return True
        except Exception as e:
            print(f"Error deleting metadata: {str(e)}")
            return False

    ## just for compatibility
    def list_node_types(self) -> List[str]:
        return self.list_node_types_recursive()


    def list_node_types_recursive(self) -> List[str]:
        """
        Recursively scan subfolders for .json files, returning
        paths as "subdir/filename" (minus .json).
        """
        types = []
        for root, _, files in os.walk(self._metadata_dir):
            for filename in files:
                if filename.endswith(".json"):
                    relative_path = os.path.relpath(root, self._metadata_dir)
                    relative_slash = relative_path.replace("\\", "/")
                    name_only = filename.replace(".json", "")
                    if relative_slash != ".":
                        full_type = f"{relative_slash}/{name_only}"
                    else:
                        full_type = name_only
                    types.append(full_type)
        return sorted(types)