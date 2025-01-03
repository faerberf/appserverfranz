# API and Schema Versioning Guide

## Overview

This document describes the versioning system used in the application server. The system provides:

- API version management
- Schema evolution
- Backward and forward compatibility
- Automatic type conversion
- Storage-agnostic versioning

## Table of Contents

1. [Concepts](#concepts)
2. [Schema Evolution](#schema-evolution)
3. [API Versioning](#api-versioning)
4. [Type System](#type-system)
5. [Compatibility Modes](#compatibility-modes)
6. [Usage Examples](#usage-examples)

## Concepts

### Field Numbers

Like Protocol Buffers, we use field numbers to ensure stability:

```json
{
  "fields": {
    "order_id": {
      "field_number": 1,
      "type": "TEXT",
      "required": true
    }
  }
}
```

Field numbers:
- Must be unique within a node type
- Never change once assigned
- Allow safe schema evolution

### Validation Modes

Three validation modes are supported:

1. `STRICT`: Exact type match required
2. `COERCE`: Attempt type conversion
3. `LOOSE`: Accept compatible values

## Schema Evolution

### Version Definition

```json
{
  "version": 2,
  "compatibility": "FORWARD",
  "valid_from": "2024-01-01T00:00:00Z",
  "fields": {
    "field_name": {
      "field_number": 1,
      "type": "TEXT",
      "required": true,
      "validation_mode": "STRICT"
    }
  }
}
```

### Upgrade Definitions

```json
{
  "upgrades": [
    {
      "from_version": 1,
      "to_version": 2,
      "changes": [
        {
          "type": "add_field",
          "field": "new_field",
          "default": "default_value"
        },
        {
          "type": "modify_field",
          "field": "existing_field",
          "changes": {
            "type": "DECIMAL",
            "validation_mode": "COERCE"
          }
        }
      ]
    }
  ]
}
```

## API Versioning

### Version Registration

```python
version_manager = APIVersionManager()

# Register node types
version_manager.register_node_type(
    "sales_order_header",
    SchemaEvolution([header_v1, header_v2])
)

# Register API versions
version_manager.register_version(
    "v1",
    {
        "sales_order_header": 1,
        "sales_order_item": 1
    },
    datetime(2024, 1, 1)
)
```

### Request/Response Flow

1. Client sends request with API version
2. Request data converted to latest schema
3. Business logic processes data
4. Response converted back to API version
5. Client receives version-appropriate data

## Type System

### Supported Types

- TEXT
- INTEGER
- FLOAT
- DECIMAL
- BOOLEAN
- DATE
- TIMESTAMP

### Type Conversion Rules

```python
CONVERSION_RULES = {
    FieldType.TEXT: {FieldType.TEXT},
    FieldType.INTEGER: {
        FieldType.INTEGER,
        FieldType.FLOAT,
        FieldType.DECIMAL,
        FieldType.TEXT
    },
    FieldType.FLOAT: {FieldType.FLOAT, FieldType.TEXT},
    FieldType.DECIMAL: {FieldType.DECIMAL, FieldType.FLOAT, FieldType.TEXT},
    FieldType.BOOLEAN: {FieldType.BOOLEAN, FieldType.TEXT},
    FieldType.DATE: {FieldType.DATE, FieldType.TIMESTAMP, FieldType.TEXT},
    FieldType.TIMESTAMP: {FieldType.TIMESTAMP, FieldType.TEXT}
}
```

## Compatibility Modes

### STRICT Mode

- All fields must match exactly
- No additional fields allowed
- Types must match exactly

### FORWARD Mode

- New fields must be optional
- Old required fields preserved
- Type promotions allowed

### BACKWARD Mode

- Old clients must work
- New required fields need defaults
- Type conversions supported

### FULL Mode

- Both forward and backward compatible
- Most flexible but most restrictive
- Best for stable APIs

## Usage Examples

### Creating a New Order

```python
# Initialize API
sales_order = SalesOrder(generator, storage, version_manager)

# Create order with v1 API
order_data = {
    "order_id": "123",
    "customer_id": "456",
    "total_amount": "100.50"
}

items_data = [
    {
        "item_id": "1",
        "product_id": "789",
        "quantity": 2,
        "unit_price": "50.25"
    }
]

# API handles version conversion
result = sales_order.create_order("v1", order_data, items_data)
```

### Reading with Different Versions

```python
# Read with v1 API
order_v1 = sales_order.get_order("v1", "123")

# Same order with v2 API
order_v2 = sales_order.get_order("v2", "123")

# Data automatically converted to appropriate version
```

## Best Practices

1. **Field Numbers**
   - Assign sequential numbers
   - Never reuse numbers
   - Reserve ranges for future use

2. **Compatibility**
   - Start with FORWARD compatibility
   - Use FULL for stable APIs
   - Provide defaults for new fields

3. **Type Conversion**
   - Use COERCE for numeric fields
   - Use STRICT for enums/IDs
   - Document conversion rules

4. **API Versions**
   - Version major changes only
   - Support at least N-1 version
   - Plan deprecation timeline

## Error Handling

```python
try:
    result = sales_order.create_order("v1", order_data, items_data)
except ValidationError as e:
    # Handle validation errors
    print(f"Field '{e.field}': {str(e)}")
except ValueError as e:
    # Handle business logic errors
    print(f"Error: {str(e)}")
```
