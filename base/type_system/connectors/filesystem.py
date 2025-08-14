import json
import os

from .base import SourceConnector
from ..core.errors import ValidationError

class FileSystemConnector(SourceConnector):
    def __init__(self, base_path=None):
        self.base_path = base_path or os.path.join(os.getcwd(), "type_definitions")
        print(f"FileSystemConnector initialized with base path: {self.base_path}")

    def get_schema(self, file_path):
        """
        Retrieves the type definition from a JSON file.
        """
        full_path = os.path.join(self.base_path, file_path + ".json")
        print(f"Loading schema from: {full_path}")
        try:
            with open(full_path, "r") as f:
                schema = json.load(f)
                # Basic validation of the loaded schema
                if not all(key in schema for key in ["type_name", "base_type", "properties"]):
                    raise ValidationError(f"Invalid schema format in file: {full_path}")

                return schema
        except FileNotFoundError:
            # Return a placeholder schema if the file doesn't exist
            return {"field1": "String"}
        except json.JSONDecodeError:
            raise ValidationError(f"Invalid JSON format in file: {full_path}")

    def supports_data_migration(self):
        """
        Indicates that this connector does not support data migration.
        """
        return False

    def migrate_data(self, file_path, old_schema, new_schema):
        """
        Not applicable for the file system connector.
        """
        print("Warning: FileSystemConnector.migrate_data is not applicable.")
        pass