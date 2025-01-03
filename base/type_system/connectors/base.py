# Abstract base class for connectors.
from abc import ABC, abstractmethod

class SourceConnector(ABC):
    @abstractmethod
    def get_schema(self, source_identifier):
        """
        Retrieves the schema for a given source identifier.

        Args:
            source_identifier (str): The identifier for the source (e.g., table name, API endpoint).

        Returns:
            dict: The schema definition.
        """
        pass

    @abstractmethod
    def supports_data_migration(self):
        """
        Returns True if this connector supports data migration, False otherwise.

        Returns:
            bool
        """
        pass

    @abstractmethod
    def migrate_data(self, source_identifier, old_schema, new_schema):
        """
        Migrates data from the old schema to the new schema.

        Args:
            source_identifier (str): The identifier for the source.
            old_schema (dict): The old schema definition.
            new_schema (dict): The new schema definition.
        """
        pass