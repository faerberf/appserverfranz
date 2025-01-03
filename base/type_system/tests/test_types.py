# Unit tests for types module.
import unittest
from core.types import define_type, get_type, validate, ValidationError, type_registry
from core.events import register_event_handler, trigger_event
from type_system.definitions.basic_types import is_valid_email
from type_system.definitions import basic_types, business, finance, products

class TestTypeSystem(unittest.TestCase):

    def setUp(self):
        # Reset the type registry before each test
        type_registry.clear()
        # Reload the modules to ensure a clean state - needed because of the global nature of the define_type approach
        import importlib
        importlib.reload(basic_types)
        importlib.reload(business)
        importlib.reload(finance)
        importlib.reload(products)

    def test_define_basic_type(self):
        define_type(type_name="MyString", base_type=str)
        self.assertIn("MyString", type_registry)

    def test_define_composite_type(self):
        define_type(type_name="MyString", base_type=str)
        define_type(type_name="MyInt", base_type=int)
        define_type(
            type_name="MyComposite",
            base_type=dict,
            properties={"name": "MyString", "value": "MyInt"}
        )
        self.assertIn("MyComposite", type_registry)

    def test_get_type(self):
        define_type(type_name="MyString", base_type=str)
        retrieved_type = get_type("MyString")
        self.assertEqual(retrieved_type["type_name"], "MyString")

    def test_validation_success(self):
        define_type(type_name="MyInt", base_type=int)
        validated_value = validate(123, "MyInt")
        self.assertEqual(validated_value, 123)

    def test_validation_failure(self):
        define_type(type_name="MyString", base_type=str)
        with self.assertRaises(ValidationError):
            validate(123, "MyString")

    def test_composite_type_validation(self):
        define_type(type_name="MyString", base_type=str)
        define_type(type_name="MyInt", base_type=int)
        define_type(
            type_name="MyComposite",
            base_type=dict,
            properties={"name": "MyString", "value": "MyInt"}
        )
        valid_data = {"name": "test", "value": 123}
        validated_data = validate(valid_data, "MyComposite")
        self.assertEqual(validated_data, valid_data)

        invalid_data = {"name": 123, "value": "test"}
        with self.assertRaises(ValidationError):
            validate(invalid_data, "MyComposite")

    def test_parent_type(self):
        define_type(type_name="ParentType", base_type=int, constraints={"min_value": 0})
        define_type(type_name="ChildType", base_type=int, parent_type="ParentType", constraints={"max_value": 100})
        child_type = get_type("ChildType")
        self.assertEqual(child_type["constraints"], {"min_value": 0, "max_value": 100})

    def test_enum_type(self):
        define_type(type_name="MyEnum", base_type=str, enum_values=["A", "B", "C"])
        self.assertEqual(validate("A", "MyEnum"), "A")
        with self.assertRaises(ValidationError):
            validate("D", "MyEnum")

    def test_nullable_type(self):
        define_type(type_name="NullableString", base_type=str, parent_type="Optional[String]")
        self.assertEqual(validate(None, "NullableString"), None)
        self.assertEqual(validate("test", "NullableString"), "test")

    def test_list_type(self):
        define_type(type_name="ListOfInt", base_type=list, parent_type="List[Integer]")
        self.assertEqual(validate([1, 2, 3], "ListOfInt"), [1, 2, 3])
        with self.assertRaises(ValidationError):
            validate([1, "a", 3], "ListOfInt")

    def test_dictionary_type(self):
        define_type(type_name="StringToIntDict", base_type=dict, parent_type="Dictionary[String, Integer]")
        self.assertEqual(validate({"a": 1, "b": 2}, "StringToIntDict"), {"a": 1, "b": 2})
        with self.assertRaises(ValidationError):
            validate({"a": "b", "c": 2}, "StringToIntDict")

    def test_type_alias(self):
        define_type(type_name="MyString", base_type=str)
        define_type_alias("StringAlias", "MyString")
        self.assertEqual(get_type("StringAlias"), get_type("MyString"))

    def test_event_triggering(self):
        events_triggered = []

        def on_type_defined_handler(payload):
            events_triggered.append(("on_type_defined", payload))

        def on_validation_success_handler(payload):
            events_triggered.append(("on_validation_success", payload))

        register_event_handler("on_type_defined", on_type_defined_handler)
        register_event_handler("on_validation_success", on_validation_success_handler)

        define_type(type_name="MyString", base_type=str)
        validate("test", "MyString")

        self.assertEqual(len(events_triggered), 2)
        self.assertEqual(events_triggered[0][0], "on_type_defined")
        self.assertEqual(events_triggered[1][0], "on_validation_success")

    def test_constraints(self):
        define_type(type_name="ConstrainedInt", base_type=int, constraints={"min_value": 0, "max_value": 10})
        self.assertEqual(validate(5, "ConstrainedInt"), 5)
        with self.assertRaises(ValidationError):
            validate(-1, "ConstrainedInt")
        with self.assertRaises(ValidationError):
            validate(11, "ConstrainedInt")

    def test_validation_rule(self):
        def is_positive(value):
            return value > 0
        define_type(type_name="PositiveInt", base_type=int, validation_rules=[is_positive])
        self.assertEqual(validate(1, "PositiveInt"), 1)
        with self.assertRaises(ValidationError):
            validate(-1, "PositiveInt")

    def test_source_type(self):
        define_type(type_name="Product", base_type=dict, source="/masterdata/product", is_structural=True)
        product_type = get_type("Product")
        self.assertEqual(product_type["properties"]["name"], "String")  # Assuming the placeholder returns this

    def test_map_and_validate_type_decorators(self):
        from type_system.core.types import map_type, validate_type

        @map_type("TestCustomer")
        class TestCustomer:
            def __init__(self, customer_id: int, name: str):
                self.customer_id = customer_id
                self.name = name

            @validate_type
            def update_name(self, new_name: str) -> None:
                self.name = new_name
        # define the structural type.
        define_type(type_name="TestCustomer", base_type=dict, source="/masterdata/customer", is_structural=True)

        customer = TestCustomer(customer_id=123, name="Alice")
        self.assertEqual(customer.name, "Alice")

        customer.update_name("Bob")
        self.assertEqual(customer.name, "Bob")

        with self.assertRaises(ValidationError):
            customer.update_name(123)

    def test_complex_constraints(self):
        # Example using multiple constraints, including a pattern
        define_type(
            type_name="Username",
            base_type=str,
            constraints={
                "min_value": 3,
                "max_value": 20,
                "pattern": r"^[a-zA-Z0-9_]+$"  # Only alphanumeric and underscore
            }
        )
        self.assertEqual(validate("valid_user1", "Username"), "valid_user1")
        with self.assertRaises(ValidationError):
            validate("inv", "Username")  # Too short
        with self.assertRaises(ValidationError):
            validate("invalid-user", "Username")  # Invalid character
        with self.assertRaises(ValidationError):
            validate("a" * 21, "Username")  # Too long

    def test_deeply_nested_composite_types(self):
        define_type(type_name="A", base_type=dict, properties={"b": "B"})
        define_type(type_name="B", base_type=dict, properties={"c": "C"})
        define_type(type_name="C", base_type=int)

        valid_data = {"b": {"c": 123}}
        self.assertEqual(validate(valid_data, "A"), valid_data)

        invalid_data = {"b": {"c": "abc"}}
        with self.assertRaises(ValidationError):
            validate(invalid_data, "A")

    def test_multiple_inheritance(self):
        define_type(type_name="Base1", base_type=int, constraints={"min_value": 0})
        define_type(type_name="Base2", base_type=int, constraints={"max_value": 100})
        define_type(type_name="Child", base_type=int, parent_type="Base1", constraints={"allowed_values": [1,2,3,4,5]})
        define_type(type_name="GrandChild", base_type=int, parent_type="Child")

        child_type = get_type("GrandChild")
        # Child should inherit constraints from both Base1 and Base2
        self.assertEqual(child_type["constraints"]["min_value"], 0)
        self.assertEqual(child_type["constraints"]["allowed_values"], [1,2,3,4,5])

    def test_inherited_validation_rules(self):
        def is_positive(value):
            return value > 0

        def is_even(value):
            return value % 2 == 0

        define_type(type_name="PositiveInt", base_type=int, validation_rules=[is_positive])
        define_type(type_name="EvenPositiveInt", base_type=int, parent_type="PositiveInt", validation_rules=[is_even])

        even_positive_type = get_type("EvenPositiveInt")
        self.assertIn(is_positive, even_positive_type["validation_rules"])
        self.assertIn(is_even, even_positive_type["validation_rules"])

        self.assertEqual(validate(2, "EvenPositiveInt"), 2)
        with self.assertRaises(ValidationError):
            validate(1, "EvenPositiveInt")  # Odd
        with self.assertRaises(ValidationError):
            validate(-2, "EvenPositiveInt")  # Negative

    def test_email_validation(self):
        # Use the provided Email type with is_valid_email rule
        self.assertEqual(validate("test@example.com", "Email"), "test@example.com")
        with self.assertRaises(ValidationError):
            validate("invalid-email", "Email")

    def test_product_category_enum(self):
        # Use the provided ProductCategory enum
        self.assertEqual(validate("Electronics", "ProductCategory"), "Electronics")
        with self.assertRaises(ValidationError):
            validate("InvalidCategory", "ProductCategory")

    def test_address_composite_type(self):
        # Use the provided Address type
        valid_address = {"street": "123 Main St", "city": "Anytown", "zip_code": "12345", "country": "USA"}
        self.assertEqual(validate(valid_address, "Address"), valid_address)
        invalid_address = {"street": 123, "city": "Anytown", "zip_code": "12345", "country": "USA"}
        with self.assertRaises(ValidationError):
            validate(invalid_address, "Address")

    def test_customer_composite_type(self):
        # Assuming Address, PositiveInteger, String, and Email are defined
        valid_customer = {
            "customer_id": 1,
            "name": "John Doe",
            "email": "john.doe@example.com",
            "address": {"street": "123 Main St", "city": "Anytown", "zip_code": "12345", "country": "USA"},
            "status": "Active"
        }
        self.assertEqual(validate(valid_customer, "Customer"), valid_customer)

        invalid_customer = {
            "customer_id": 0,  # Invalid: should be PositiveInteger
            "name": "John Doe",
            "email": "invalid-email",  # Invalid: should be Email
            "address": {"street": "123 Main St", "city": "Anytown", "zip_code": "12345", "country": "USA"},
            "status": "Active"
        }
        with self.assertRaises(ValidationError):
            validate(invalid_customer, "Customer")

    def test_product_structural_type(self):
        # Assuming the database connector placeholder returns a predefined schema for 'products'
        product = validate({"product_id": 1, "name": "Test Product", "description": "A test product", "price": 99.99, "category": "Electronics"}, "Product")
        self.assertEqual(product["name"], "Test Product")
        with self.assertRaises(ValidationError):
            validate({"product_id": "abc", "name": "Test Product", "description": "A test product", "price": 99.99, "category": "Electronics"}, "Product") # product_id should be an integer

    def test_customer_structural_type(self):
        # Assuming the database connector placeholder returns a predefined schema for 'customers'
        customer = validate({"customer_id": 1, "name": "John Doe", "email": "john.doe@example.com", "address": {"street": "123 Main St", "city": "Anytown", "zip_code": "12345", "country": "USA"}, "status": "Active"}, "Customer")
        self.assertEqual(customer["name"], "John Doe")
        with self.assertRaises(ValidationError):
            validate({"customer_id": "abc", "name": "John Doe", "email": "john.doe@example.com", "address": {"street": "123 Main St", "city": "Anytown", "zip_code": "12345", "country": "USA"}, "status": "Active"}, "Customer")

    def test_invoice_structural_type(self):
        # Assuming the API connector placeholder returns a predefined schema for 'sales_order_api'
        invoice = validate({
            "invoice_id": 123,
            "customer": {"customer_id": 1, "name": "John Doe", "email": "john.doe@example.com", "address": {"street": "123 Main St", "city": "Anytown", "zip_code": "12345", "country": "USA"}, "status": "Active"},
            "invoice_date": "2023-10-27T12:34:56",
            "line_items": [
                {"product": {"product_id": 1, "name": "Test Product", "description": "A test product", "price": 99.99, "category": "Electronics"}, "quantity": 2, "price": 99.99, "discount": 5.0},
                {"product": {"product_id": 2, "name": "Another Product", "description": "Another test product", "price": 49.99, "category": "Books"}, "quantity": 1, "price": 49.99}
            ],
            "status": "Sent"
        }, "Invoice")
        self.assertEqual(invoice["invoice_id"], 123)
        with self.assertRaises(ValidationError):
            validate({
                "invoice_id": "abc",
                "customer": {"customer_id": 1, "name": "John Doe", "email": "john.doe@example.com", "address": {"street": "123 Main St", "city": "Anytown", "zip_code": "12345", "country": "USA"}, "status": "Active"},
                "invoice_date": "2023-10-27T12:34:56",
                "line_items": [
                    {"product": {"product_id": 1, "name": "Test Product", "description": "A test product", "price": 99.99, "category": "Electronics"}, "quantity": 2, "price": 99.99, "discount": 5.0},
                    {"product": {"product_id": 2, "name": "Another Product", "description": "Another test product", "price": 49.99, "category": "Books"}, "quantity": 1, "price": 49.99}
                ],
                "status": "Sent"
            }, "Invoice")