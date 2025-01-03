"""Main application entry point."""
from decimal import Decimal
from datetime import datetime
import os
import traceback

from base.generator import Generator
from base.metadata.api import MetadataAPI
from base.schema.evolution import SchemaEvolution
from masterdata.product import Product
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
        masterdata_generator = Generator(
            data_path,  # Use root data path
            metadata_path,  # Use root metadata path
            schema_evolution=schema_evolution
        )
        finance_generator = Generator(
            data_path,  # Use root data path
            metadata_path,  # Use root metadata path
            schema_evolution=schema_evolution
        )
        
        # Initialize services
        product_service = Product(masterdata_generator)
        order_service = SalesOrder(finance_generator)
        order_api = SalesOrderAPI(order_service, finance_generator.version_manager)
        
        # Create test data
        test_products = [
            ("P001", "Product 1", "Test product 1", Decimal("10.99"), "PC"),
            ("P002", "Product 2", "Test product 2", Decimal("20.50"), "KG"),
            ("P003", "Product 3", "Test product 3", Decimal("5.75"), "L")
        ]
        
        # Create or update test products
        for code, name, desc, price, unit in test_products:
            try:
                product_service.create(code, name, desc, price, unit)
            except ValueError:
                # Product might already exist
                pass
                
        # Create test order with 3 items
        order_data = {
            "customer_name": "Test Customer",
            "customer_email": "test@example.com",
            "customer_phone": "555-0123",
            "shipping_address": "123 Main St",
            "order_date": datetime.now().isoformat(),
            "payment_method": "credit_card",
            "_schema_version": 1
        }
        
        items_data = [
            {
                "product_code": "P001",
                "product_name": "Product 1",
                "price": "10.99",
                "quantity": "2",
                "unit": "PC",
                "_schema_version": 1
            },
            {
                "product_code": "P002",
                "product_name": "Product 2",
                "price": "20.50",
                "quantity": "1.5",
                "unit": "KG",
                "_schema_version": 1
            },
            {
                "product_code": "P003",
                "product_name": "Product 3",
                "price": "5.75",
                "quantity": "3",
                "unit": "L",
                "_schema_version": 1
            }
        ]
        
        # Create order with items
        result = order_api.create_order("v1", order_data, items_data)
        print(f"Created test order: {result}")
        
        # Update the order
        header_id = result["header_id"]
        update_data = {
            "customer_name": "Updated Customer",
            "customer_email": "updated@example.com",
            "customer_phone": "555-9999",
            "shipping_address": "456 New St",
            "order_date": datetime.now().isoformat(),
            "payment_method": "bank_transfer"
        }
        
        # Update order header
        order_api.update_order("v1", header_id, update_data)
        print(f"Updated order {header_id}")
        
        # Read and verify the updated order
        updated_order = order_api.get_order("v1", header_id)
        print(f"Updated order data: {updated_order}")
        
        return 0
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())