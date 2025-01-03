# Unit tests for connectors module.
import unittest
from type_system.connectors.base import SourceConnector
from type_system.connectors.database import DatabaseConnector
from type_system.connectors.api import APIConnector

class TestSourceConnector(unittest.TestCase):
    def test_abstract_base_class(self):
        with self.assertRaises(TypeError):
            SourceConnector()  # Cannot instantiate abstract class

class TestDatabaseConnector(unittest.TestCase):
    def test_get_schema(self):
        connector = DatabaseConnector()
        schema = connector.get_schema("products")
        self.assertIsInstance(schema, dict)
        self.assertIn("product_id", schema)

    def test_supports_data_migration(self):
        connector = DatabaseConnector()
        self.assertFalse(connector.supports_data_migration()) # Placeholder returns False

class TestAPIConnector(unittest.TestCase):
    def test_get_schema(self):
        connector = APIConnector()
        schema = connector.get_schema("some_api_endpoint")
        self.assertIsInstance(schema, dict)
        self.assertIn("field1", schema)

    def test_supports_data_migration(self):
        connector = APIConnector()
        self.assertFalse(connector.supports_data_migration())