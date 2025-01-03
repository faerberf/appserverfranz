# Example usage of the type system.
from type_system.core.types import define_type, validate, ValidationError, map_type, validate_type
from type_system.definitions import basic_types, business, finance, products
from type_system.core.events import register_event_handler

# Example usage demonstrating the type system
if __name__ == "__main__":
    # Example event handler
    def on_validation_failure_handler(payload):
        exception = payload["exception"]
        print(f"Validation failed: {exception}")

    register_event_handler("on_validation_failure", on_validation_failure_handler)

    # Basic type usage
    try:
        validate("test@example.com", "Email")
        print("Email validation successful")
    except ValidationError as e:
        print(f"Email validation failed: {e}")

    try:
        validate("invalid_email", "Email")
        print("Email validation successful")
    except ValidationError as e:
        print(f"Email validation failed: {e}")

    # Composite type usage
    address = {
        "street": "123 Main St",
        "city": "Anytown",
        "zip_code": "12345",
        "country": "USA"
    }

    try:
        validated_address = validate(address, "Address")
        print("Address validation successful")
    except ValidationError as e:
        print(f"Address validation failed: {e}")

    # Customer type usage
    customer_data = {
        "customer_id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "address": validated_address,
        "status": "Active"
    }
    try:
        validated_customer = validate(customer_data, "Customer")
        print("Customer validation successful")
    except ValidationError as e:
        print(f"Customer validation failed: {e}")

    # Decorator usage
    @map_type("ValidatedCustomer")
    class ValidatedCustomer:
        def __init__(self, customer_id: int, name: str, email: str):
            self.customer_id = customer_id
            self.name = name
            self.email = email

        @validate_type
        def update_email(self, new_email: str):
            self.email = new_email

    # Structural type usage
    try:
        validated_product = validate({"product_id": 1, "name": "Test Product", "description": "A test product", "price": 99.99, "category": "Electronics"}, "Product")
        print("Product validation successful")
    except ValidationError as e:
        print(f"Product validation failed: {e}")