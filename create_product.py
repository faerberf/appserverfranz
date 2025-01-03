"""Main application entry point."""
from decimal import Decimal
from datetime import datetime
import os
import traceback

from base.generator import Generator
from base.metadata.api import MetadataAPI
from base.schema.evolution import SchemaEvolution
from masterdata import Product
from finance import SalesOrder
from finance.sales_order import SalesOrder, SalesOrderAPI


def load_schema_evolution(metadata_path: str) -> SchemaEvolution:
    """Load schema evolution from metadata path."""
    evolution = SchemaEvolution()
    
    # Load schema evolution files
    for schema_file in [
        os.path.join(metadata_path, "global_node_definitions.json"),  # Global fields for all nodes
        os.path.join(metadata_path, "masterdata", "product.json"),
        os.path.join(metadata_path, "finance", "sales_order_header.json"),
        os.path.join(metadata_path, "finance", "sales_order_item.json")
    ]:
        if os.path.exists(schema_file):
            schema = SchemaEvolution.from_file(schema_file)
            for version in schema.get_all_versions():
                evolution.add_version(version)
                
    return evolution


def main():
    """Main application entry point."""
    try:
        print("Performing system-wide data upgrade...")
        
        # Initialize paths
        base_path = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(base_path, "data")
        metadata_path = os.path.join(base_path, "metadata")
        
        # Initialize schema evolution
        schema_evolution = load_schema_evolution(metadata_path)
        
        # Initialize generators
        print(f"Using metadata path: {metadata_path}")
        masterdata_generator = Generator(
            data_path,  # Use root data path
            metadata_path,  # Use root metadata path
            schema_evolution=schema_evolution
        )

        
        # Initialize services
        product_service = Product(masterdata_generator)

        
        # Create test data
        test_products = [
            ("P001", "Product 1", "Test product 1", Decimal("10.99"), "PC"),
            ("P002", "Product 2", "Test product 2", Decimal("20.50"), "KG"),
            ("P003", "Product 3", "Test product 3", Decimal("5.75"), "L")
        ]
        
        # Create or update test products
        for code, name, desc, price, unit in test_products:
            try:
                print(f"Creating product {code}...")
                product_id = product_service.create(code, name, desc, price, unit)
                print(f"Created product {code} with ID {product_id}")
            except ValueError as e:
                print(f"Error creating product {code}: {str(e)}")
                
        
        return 0
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())