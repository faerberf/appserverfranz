"""Extended tests for metadata API functionality."""
from typing import Dict, Any, List
import os
import shutil
import unittest
from datetime import datetime

from base.metadata.api import MetadataAPI
from base.schema.types import FieldType, ValidationMode


class TestMetadataAPIExtended(unittest.TestCase):
    """Extended test cases for MetadataAPI."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = "test_metadata_extended"
        os.makedirs(self.test_dir, exist_ok=True)
        self.api = MetadataAPI(self.test_dir)
        
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    def test_create_metadata_basic(self):
        """Test basic metadata creation."""
        fields = [
            {
                "name": "name",
                "type": "string",
                "description": "Name of item",
                "required": True,
                "validation_mode": "strict"
            }
        ]
        
        # Test creation
        self.assertTrue(
            self.api.create_metadata("test/item", fields, "Test metadata", _schema_version=1)
        )
        
        # Verify created metadata
        metadata = self.api.get_metadata("test/item")
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["_schema_version"], 1)
        self.assertEqual(len(metadata["versions"]), 1)
        
    def test_create_metadata_duplicate(self):
        """Test creating duplicate metadata."""
        fields = [{"name": "test", "type": "string"}]
        
        # Create initial metadata
        self.api.create_metadata("test/duplicate", fields)
        
        # Attempt to create duplicate
        with self.assertRaises(ValueError):
            self.api.create_metadata("test/duplicate", fields)
            
    def test_update_nonexistent_metadata(self):
        """Test updating non-existent metadata."""
        with self.assertRaises(ValueError):
            self.api.update_metadata("test/nonexistent", [{"name": "test", "type": "string"}])
            
    def test_version_increment(self):
        """Test version incrementing behavior."""
        # Create initial metadata
        initial_fields = [{"name": "field1", "type": "string"}]
        self.api.create_metadata("test/version", initial_fields, _schema_version=1)
        
        # Update with new fields
        new_fields = [{"name": "field2", "type": "string"}]
        self.api.update_metadata("test/version", new_fields, _schema_version=2)
        
        # Verify version increment
        metadata = self.api.get_metadata("test/version")
        self.assertEqual(metadata["_schema_version"], 2)
        self.assertEqual(len(metadata["versions"]), 2)
        
    def test_invalid_field_type(self):
        """Test handling of invalid field types."""
        fields = [{
            "name": "invalid",
            "type": "nonexistent_type",  # Invalid type
            "required": True
        }]
        
        with self.assertRaises(ValueError):
            self.api.create_metadata("test/invalid", fields)
            
    def test_empty_fields(self):
        """Test creating metadata with no fields."""
        with self.assertRaises(ValueError):
            self.api.create_metadata("test/empty", [])
            
    def test_complex_upgrade_path(self):
        """Test complex upgrade path with multiple versions."""
        # Version 1
        v1_fields = [{"name": "name", "type": "string"}]
        self.api.create_metadata("test/upgrade", v1_fields, _schema_version=1)
        
        # Version 2: Add optional field
        v2_fields = [
            {"name": "name", "type": "string"},
            {"name": "description", "type": "string", "required": False}
        ]
        self.api.update_metadata(
            "test/upgrade",
            v2_fields,
            _schema_version=2,
            upgrade_definitions={"description": {"type": "default", "value": ""}}
        )
        
        # Version 3: Make field required
        v3_fields = [
            {"name": "name", "type": "string"},
            {"name": "description", "type": "string", "required": True}
        ]
        self.api.update_metadata(
            "test/upgrade",
            v3_fields,
            _schema_version=3,
            upgrade_definitions={"description": {"type": "default", "value": "No description"}}
        )
        
        # Verify upgrade path
        metadata = self.api.get_metadata("test/upgrade")
        self.assertEqual(metadata["_schema_version"], 3)
        self.assertEqual(len(metadata["versions"]), 3)
        
    def test_metadata_with_constraints(self):
        """Test metadata with field constraints."""
        fields = [
            {
                "name": "age",
                "type": "integer",
                "required": True,
                "constraints": {
                    "min": 0,
                    "max": 150
                }
            },
            {
                "name": "email",
                "type": "string",
                "required": True,
                "constraints": {
                    "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                }
            }
        ]
        
        # Create metadata with constraints
        self.assertTrue(
            self.api.create_metadata("test/constraints", fields, _schema_version=1)
        )
        
        # Verify constraints are preserved
        metadata = self.api.get_metadata("test/constraints")
        self.assertIsNotNone(metadata)
        version = next(iter(metadata["versions"].values()))
        age_field = version["fields"]["age"]
        self.assertEqual(age_field["constraints"]["min"], 0)
        self.assertEqual(age_field["constraints"]["max"], 150)
        email_field = version["fields"]["email"]
        self.assertEqual(
            email_field["constraints"]["pattern"],
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )
        
    def test_invalid_node_type(self):
        """Test creating metadata with invalid node type."""
        fields = [{"name": "test", "type": "string"}]
        invalid_types = [
            "",  # Empty
            "/",  # Just separator
            "invalid/",  # Trailing separator
            "/invalid",  # Leading separator
            "invalid//type",  # Double separator
            "invalid/type/",  # Trailing separator
            "invalid/type/extra"  # Too many components
        ]
        
        for invalid_type in invalid_types:
            with self.assertRaises(ValueError):
                self.api.create_metadata(invalid_type, fields)
                
    def test_field_name_conflicts(self):
        """Test handling of field name conflicts."""
        # Create initial version
        v1_fields = [
            {"name": "id", "type": "string"},
            {"name": "name", "type": "string"}
        ]
        self.api.create_metadata("test/conflicts", v1_fields, _schema_version=1)
        
        # Try to update with conflicting field names
        v2_fields = [
            {"name": "id", "type": "string"},
            {"name": "id", "type": "integer"}  # Duplicate name
        ]
        with self.assertRaises(ValueError):
            self.api.update_metadata("test/conflicts", v2_fields)
            
    def test_version_downgrade(self):
        """Test preventing version downgrade."""
        # Create metadata with version 2
        fields = [{"name": "test", "type": "string"}]
        self.api.create_metadata("test/downgrade", fields, _schema_version=2)
        
        # Try to update with lower version
        with self.assertRaises(ValueError):
            self.api.update_metadata("test/downgrade", fields, _schema_version=1)


def main():
    """Run the tests."""
    unittest.main(module=__name__, argv=[''], verbosity=2, exit=False)


if __name__ == "__main__":
    main()
