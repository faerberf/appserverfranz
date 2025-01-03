# Business-related types (e.g., Customer, Invoice).
from type_system.core.types import define_type
from type_system.definitions.basic_types import String, PositiveInteger, Email

# Address type
define_type(
    type_name="Address",
    base_type=dict,
    properties={
        "street": "String",
        "city": "String",
        "zip_code": "String",
        "country": "String"
    },
    description="A postal address."
)

# Customer type
define_type(
    type_name="Customer",
    base_type=dict,
    properties={
        "customer_id": "PositiveInteger",
        "name": "String",
        "email": "Email",
        "address": "Address",
        "status": "CustomerStatus"
    },
    description="Represents a customer."
)

define_type(
    type_name="CustomerStatus",
    base_type=str,
    enum_values=["Active", "Inactive", "Suspended"],
    description="Represents the status of a customer."
)

# Invoice Status
define_type(
    type_name="InvoiceStatus",
    base_type=str,
    enum_values=["Draft", "Sent", "Paid", "Overdue", "Cancelled"],
    description="Represents the status of an invoice."
)

# Invoice Line Item
define_type(
    type_name="InvoiceLineItem",
    base_type=dict,
    properties={
        "product": "Product",
        "quantity": "PositiveInteger",
        "price": "PositiveFloat",
        "discount": "Optional[PositiveFloat]"
    },
    description="Represents a single line item in an invoice."
)
# Invoice Line Item List
define_type(
    type_name="InvoiceLineItemList",
    base_type=list,
    parent_type="List[InvoiceLineItem]",
    description="A list of invoice line items"
)

# Invoice type
define_type(
    type_name="Invoice",
    base_type=dict,
    properties={
        "invoice_id": "PositiveInteger",
        "customer": "Customer",
        "invoice_date": "DateTime",
        "line_items": "InvoiceLineItemList",
        "status": "InvoiceStatus"
    },
    description="Represents an invoice."
)

# PaymentMethod
define_type(
    type_name="PaymentMethod",
    base_type=str,
    enum_values=["CreditCard", "BankAccount", "PayPal", "Other"],
    description="Represents the method of a payment."
)

# Payment
define_type(
    type_name="Payment",
    base_type=dict,
    properties={
        "payment_id": "PositiveInteger",
        "invoice": "Invoice",
        "payment_date": "DateTime",
        "amount": "PositiveFloat",
        "payment_method": "PaymentMethod"
    },
    description="Represents a payment."
)

# User Roles
define_type(
    type_name="UserRole",
    base_type=str,
    enum_values=["Admin", "Sales", "CustomerSupport", "Guest"],
    description="Represents the role of a user."
)
# User Roles List
define_type(
    type_name="UserRolesList",
    base_type=list,
    parent_type="List[UserRole]",
    description="A list of user roles."
)

# User
define_type(
    type_name="User",
    base_type=dict,
    properties={
        "user_id": "PositiveInteger",
        "username": "String",
        "email": "Email",
        "password": "StrongPassword",
        "roles": "UserRolesList"
    },
    description="Represents a user account."
)

# Supplier
define_type(
    type_name="Supplier",
    base_type=dict,
    properties={
        "supplier_id": "PositiveInteger",
        "name": "String",
        "contact_email": "Email",
        "address": "Address"
    },
    description="Represents a supplier."
)

#Product type (structural, loaded from node definition)
define_type(
    type_name="Product",
    base_type=dict,
    source="/masterdata/product",
    is_structural=True,
    description="Represents a product."
)

# Customer type (structural, loaded from node definition)
define_type(
    type_name="Customer",
    base_type=dict,
    source="/masterdata/customer",
    is_structural=True,
    description="Represents a customer."
)

# Invoice type (structural, loaded from node definition)
define_type(
    type_name="Invoice",
    base_type=dict,
    source="/finance/sales_order",
    is_structural=True,
    description="Represents an invoice."
)

# Order type (structural, loaded from file system)
define_type(
    type_name="Order",
    base_type=dict,
    source="/file_system/order",
    is_structural=True,
    description="Represents an order."
)

# OrderItem type (structural, loaded from file system)
define_type(
    type_name="OrderItem",
    base_type=dict,
    source="/file_system/orderitem",
    is_structural=True,
    description="Represents an item in an order."
)

# OrderItemList type (structural, loaded from file system)
define_type(
    type_name="OrderItemList",
    base_type=list,
    source="/file_system/orderitemlist",
    is_structural=True,
    description="A list of order items."
)