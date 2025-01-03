"""Examples of using the versioning system."""
from datetime import datetime
from decimal import Decimal
from base.storage.filesystem import FileSystemStorage
from base.api.version import APIVersionManager
from base.schema.evolution import SchemaEvolution
from base.schema.types import FieldType, ValidationMode
from finance.sales_order import SalesOrder


def setup_version_manager():
    """Set up version manager with example schemas."""
    # Create storage
    storage = FileSystemStorage("/path/to/storage")
    
    # Create version manager
    version_manager = APIVersionManager()
    
    # Define schema versions
    header_v1 = {
        "version": 1,
        "compatibility": "FORWARD",
        "fields": {
            "order_id": {
                "field_number": 1,
                "type": "TEXT",
                "required": True,
                "validation_mode": "STRICT"
            },
            "total_amount": {
                "field_number": 2,
                "type": "FLOAT",
                "required": True,
                "validation_mode": "COERCE"
            }
        }
    }
    
    header_v2 = {
        "version": 2,
        "compatibility": "FORWARD",
        "fields": {
            "order_id": {
                "field_number": 1,
                "type": "TEXT",
                "required": True,
                "validation_mode": "STRICT"
            },
            "total_amount": {
                "field_number": 2,
                "type": "DECIMAL",
                "required": True,
                "validation_mode": "COERCE",
                "constraints": {
                    "precision": 2
                }
            },
            "status": {
                "field_number": 3,
                "type": "TEXT",
                "required": True,
                "validation_mode": "STRICT",
                "default": "PENDING",
                "constraints": {
                    "allowed_values": [
                        "PENDING",
                        "CONFIRMED",
                        "SHIPPED"
                    ]
                }
            }
        }
    }
    
    # Register schemas
    version_manager.register_node_type(
        "sales_order_header",
        SchemaEvolution([header_v1, header_v2])
    )
    
    # Register API versions
    version_manager.register_version(
        "v1",
        {"sales_order_header": 1},
        datetime(2024, 1, 1)
    )
    
    version_manager.register_version(
        "v2",
        {"sales_order_header": 2},
        datetime(2024, 7, 1)
    )
    
    return storage, version_manager


def example_create_order():
    """Example of creating an order with different API versions."""
    # Set up components
    storage, version_manager = setup_version_manager()
    sales_order = SalesOrder(None, storage, version_manager)
    
    # Create order with v1 API
    order_v1 = {
        "order_id": "123",
        "total_amount": 100.50
    }
    
    result_v1 = sales_order.create_order("v1", order_v1, [])
    print("V1 Order:", result_v1)
    
    # Create order with v2 API
    order_v2 = {
        "order_id": "124",
        "total_amount": "200.75",
        "status": "CONFIRMED"
    }
    
    result_v2 = sales_order.create_order("v2", order_v2, [])
    print("V2 Order:", result_v2)
    
    # Read v2 order with v1 API
    result_v1_read = sales_order.get_order("v1", "124")
    print("V2 Order read with V1 API:", result_v1_read)


def example_type_conversion():
    """Example of type conversion between versions."""
    storage, version_manager = setup_version_manager()
    sales_order = SalesOrder(None, storage, version_manager)
    
    # Create with v1 (FLOAT)
    order_v1 = {
        "order_id": "125",
        "total_amount": 300.99
    }
    
    result_v1 = sales_order.create_order("v1", order_v1, [])
    print("Created with V1 (FLOAT):", result_v1)
    
    # Read with v2 (DECIMAL)
    result_v2 = sales_order.get_order("v2", "125")
    print("Read with V2 (DECIMAL):", result_v2)
    
    # Verify precision
    amount = result_v2["order"]["total_amount"]
    assert isinstance(amount, Decimal)
    assert str(amount) == "300.99"


def example_validation():
    """Example of validation with different modes."""
    storage, version_manager = setup_version_manager()
    sales_order = SalesOrder(None, storage, version_manager)
    
    try:
        # Try to create invalid v2 order
        order_invalid = {
            "order_id": "126",
            "total_amount": "invalid",
            "status": "INVALID_STATUS"
        }
        
        sales_order.create_order("v2", order_invalid, [])
        
    except ValueError as e:
        print("Validation error:", str(e))
        
    # Create valid order
    order_valid = {
        "order_id": "126",
        "total_amount": "500.00",
        "status": "PENDING"
    }
    
    result = sales_order.create_order("v2", order_valid, [])
    print("Valid order:", result)


if __name__ == "__main__":
    print("Creating orders with different versions:")
    example_create_order()
    print("\nType conversion example:")
    example_type_conversion()
    print("\nValidation example:")
    example_validation()
