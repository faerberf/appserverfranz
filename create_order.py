"""Main application entry point."""
from decimal import Decimal
from datetime import datetime
import os
import traceback

from base.generator import Generator
from base.metadata.api import MetadataAPI
from base.schema.evolution import SchemaEvolution


from finance.sales_order import SalesOrder, SalesOrderAPI


def load_schema_evolution(metadata_path: str) -> SchemaEvolution:
    """Load schema evolution from metadata path."""
    evolution = SchemaEvolution()
    
    # Load schema evolution files
    for schema_file in [
        os.path.join(metadata_path, "global_node_definitions.json"),  # Global fields for all nodes

        os.path.join(metadata_path, "finance", "sales_order_header.json"),
        os.path.join(metadata_path, "finance", "sales_order_item.json"),

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


        
        finance_generator = Generator(
            data_path,  # Use root data path
            metadata_path,  # Use root metadata path
            schema_evolution=schema_evolution
        )
        
        # Initialize services


        
        order_service = SalesOrder(finance_generator)
        order_api = SalesOrderAPI(order_service, finance_generator.version_manager)
        
        # Create test data
        

        
        # Create test order with 1 item
        order_data = {
            "customer_name": "Test Customer",
            "customer_email": "test@example.com",
            "customer_phone": "555-0123",
            "shipping_address": "123 Main St",
            "order_date": datetime.now().isoformat(),
            "payment_method": "credit_card",
            "_schema_version": 2
        }
        
        items_data = [
            {
                "product_code": "P001",
                "product_name": "Product 1",
                "price": "10.99",
                "quantity": "2",
                "unit": "PC",
                "_schema_version": 2
            }
        ]
        
        # Create order with items
        result = order_api.create_order("v1", order_data, items_data)
        print(f"Created test order: {result}")
        
        
        return 0
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())