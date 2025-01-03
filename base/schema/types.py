"""Schema type definitions and type conversion system."""
from enum import Enum, auto
from typing import Any, Dict, Optional, Type, Union
from decimal import Decimal


class FieldType(str, Enum):
    """Supported field types with conversion rules."""
    
    STRING = "string"
    TEXT = "TEXT"  # Alias for string, used in metadata files
    INTEGER = "integer"
    DECIMAL = "decimal"
    FLOAT = "FLOAT"  # Alias for decimal, used in metadata files
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "DATE"  # Date without time
    TIMESTAMP = "TIMESTAMP"  # Full date and time
    LIST = "list"
    DICT = "dict"
    REFERENCE = "reference"
    
    @classmethod
    def can_convert(cls, from_type: 'FieldType', to_type: 'FieldType') -> bool:
        """Check if conversion between types is allowed."""
        # Define conversion rules
        CONVERSION_RULES = {
            cls.STRING: {cls.STRING, cls.TEXT},  # String can convert to TEXT
            cls.TEXT: {cls.STRING, cls.TEXT},  # TEXT can convert to string
            cls.INTEGER: {cls.INTEGER, cls.DECIMAL, cls.FLOAT, cls.STRING, cls.TEXT},  # Integer can convert to decimal/float/string
            cls.DECIMAL: {cls.DECIMAL, cls.FLOAT, cls.STRING, cls.TEXT},  # Decimal can convert to float/string
            cls.FLOAT: {cls.DECIMAL, cls.FLOAT, cls.STRING, cls.TEXT},  # Float can convert to decimal/string
            cls.BOOLEAN: {cls.BOOLEAN, cls.STRING, cls.TEXT},  # Boolean can convert to string
            cls.DATETIME: {cls.DATETIME, cls.DATE, cls.TIMESTAMP, cls.STRING, cls.TEXT},  # Datetime can convert to string/date/timestamp
            cls.DATE: {cls.DATE, cls.DATETIME, cls.TIMESTAMP, cls.STRING, cls.TEXT},  # Date can convert to datetime/timestamp/string
            cls.TIMESTAMP: {cls.TIMESTAMP, cls.DATETIME, cls.DATE, cls.STRING, cls.TEXT},  # Timestamp can convert to datetime/date/string
            cls.LIST: {cls.LIST},  # List can only convert to list
            cls.DICT: {cls.DICT},  # Dict can only convert to dict
            cls.REFERENCE: {cls.REFERENCE}  # Reference can only convert to reference
        }
        return to_type in CONVERSION_RULES.get(from_type, set())


class CompatibilityMode(Enum):
    """Schema compatibility modes."""
    
    STRICT = "strict"  # All fields required, no additional fields
    FORWARD = "forward"  # New fields optional, old fields required
    BACKWARD = "backward"  # Old fields must work, new fields allowed
    FULL = "full"  # Both forward and backward compatibility


class ValidationMode(str, Enum):
    """Field validation modes."""
    
    NONE = "none"
    STRICT = "strict"
    LENIENT = "lenient"
    COERCE = "coerce"  # Attempt type coercion if needed
    LOOSE = "loose"  # Accept any compatible value


class TypeConverter:
    """Handles type conversion between different field types."""
    
    @staticmethod
    def convert(value: Any, from_type: FieldType, to_type: FieldType) -> Any:
        """Convert a value from one type to another."""
        if not FieldType.can_convert(from_type, to_type):
            raise ValueError(f"Cannot convert from {from_type} to {to_type}")
            
        if value is None:
            return None
            
        try:
            # Handle STRING target type first
            if to_type == FieldType.STRING:
                return str(value)
                
            # Handle numeric conversions
            if to_type == FieldType.INTEGER:
                return int(float(value))  # Convert through float to handle string decimals
            elif to_type == FieldType.DECIMAL:
                return Decimal(str(value))  # Convert through string to maintain precision
                
            # Handle boolean
            if to_type == FieldType.BOOLEAN:
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
                
            # No conversion needed
            return value
            
        except (ValueError, TypeError, DecimalException) as e:
            raise ValueError(f"Conversion failed from {from_type} to {to_type}: {str(e)}")


class FieldDefinition:
    """Definition of a field in a schema."""
    
    def __init__(
            self,
            name: str,
            field_type: FieldType,
            required: bool = False,
            validation_mode: ValidationMode = ValidationMode.NONE,
            default_value: Any = None,
            description: str = "",
            constraints: Dict[str, Any] = None
        ):
        """Initialize field definition."""
        self.name = name
        self.field_type = field_type
        self.required = required
        self.validation_mode = validation_mode
        self.default_value = default_value
        self.description = description
        self.constraints = constraints or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert field definition to dictionary."""
        return {
            "name": self.name,
            "type": self.field_type.value,
            "required": self.required,
            "validation": self.validation_mode.value,
            "default": self.default_value,
            "description": self.description,
            "constraints": self.constraints
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FieldDefinition":
        """Create field definition from dictionary."""
        # Extract known constraints from the data
        constraints = {}
        constraint_fields = [
            "max_length", "min_length", "format", 
            "allowed_values", "min_value", "max_value",
            "field_number"
        ]
        for field in constraint_fields:
            if field in data:
                constraints[field] = data[field]
                
        return cls(
            name=data["name"],
            field_type=FieldType(data["type"]),
            required=data.get("required", False),
            validation_mode=ValidationMode(data.get("validation", "none")),
            default_value=data.get("default"),
            description=data.get("description", ""),
            constraints=constraints
        )
