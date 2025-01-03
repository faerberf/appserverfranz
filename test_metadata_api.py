"""Test script for metadata API."""
import os
from base.metadata.api import MetadataAPI


def main():
    """Main test function."""
    try:
        # Initialize API
        metadata_dir = os.path.join(os.path.dirname(__file__), "metadata")
        api = MetadataAPI(metadata_dir)
        
        # Create test metadata
        test_fields = [
            {
                "name": "name",
                "type": "string",
                "description": "Name of item",
                "required": True,
                "validation_mode": "strict"
            },
            {
                "name": "price",
                "type": "decimal",
                "description": "Price of item",
                "required": True,
                "validation_mode": "strict",
                "constraints": {
                    "min": "0"
                }
            },
            {
                "name": "description",
                "type": "string",
                "description": "Item description",
                "required": False
            }
        ]
        
        # Create metadata
        print("Creating test metadata...")
        api.create_metadata(
            "test/item",
            test_fields,
            "Test item metadata",
            _schema_version=1
        )
        
        # Read metadata
        print("\nReading metadata...")
        metadata = api.get_metadata("test/item")
        print(f"Metadata: {metadata}")
        
        # Update metadata with new fields
        print("\nUpdating metadata...")
        new_fields = test_fields + [
            {
                "name": "category",
                "type": "string",
                "description": "Item category",
                "required": True
            }
        ]
        api.update_metadata(
            "test/item",
            fields=new_fields,
            description="Updated test item metadata",
            _schema_version=2,
            upgrade_definitions={
                "category": {
                    "type": "default",
                    "value": "uncategorized"
                }
            }
        )
        
        # Read updated metadata
        print("\nReading updated metadata...")
        metadata = api.get_metadata("test/item")
        print(f"Updated metadata: {metadata}")
        
        # List all node types
        print("\nListing node types...")
        node_types = api.list_node_types()
        print(f"Node types: {node_types}")
        
        # Clean up
        print("\nCleaning up...")
        api.delete_metadata("test/item")
        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
