"""Data validation functionality."""
from decimal import Decimal
from typing import Dict, Any, Optional, List, Tuple
from typing import Union
from .schema.types import FieldDefinition, FieldType, ValidationMode, TypeConverter
from .schema.evolution import SchemaVersion


class ValidationError(Exception):
    """Validation error with details."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        """Initialize validation error.
        
        Args:
            message: Error message
            field: Field that caused the error
        """
        self.field = field
        super().__init__(message)


def validate_data(data: Dict[str, Any], schema: Union[SchemaVersion, Dict[str, Any]], strict: bool = False) -> Union[bool, List[ValidationError]]:
    """Validate data against schema.
    
    Args:
        data: Data to validate
        schema: Schema version to validate against (SchemaVersion object or dictionary)
        strict: Whether to enforce strict validation
        
    Returns:
        Union[bool, List[ValidationError]]: True if valid, or list of validation errors
    """
    # Convert dictionary to SchemaVersion if needed
    if isinstance(schema, dict):
        schema = SchemaVersion.from_dict(schema)
    
    validator = Validator(schema)
    errors = validator.validate(data, strict)
    return True if not errors else errors


class Validator:
    """Validates data against schema version."""
    
    def __init__(self, schema: SchemaVersion):
        """Initialize with schema version."""
        self.schema = schema
        
    def validate(self, data: Dict[str, Any], strict: bool = False) -> List[ValidationError]:
        """Validate data against schema.
        
        Args:
            data: Data to validate
            strict: Whether to enforce strict validation
            
        Returns:
            List[ValidationError]: List of validation errors
        """
        errors = []
        
        # Check required fields
        for name, field in self.schema.fields.items():
            if field.required and name not in data:
                errors.append(
                    ValidationError(f"Required field '{name}' is missing", name)
                )
                
        # Validate each field
        for name, value in data.items():
            field = self.schema.fields.get(name)
            
            # Unknown field
            if not field:
                if strict:
                    errors.append(
                        ValidationError(f"Unknown field '{name}'", name)
                    )
                continue
                
            # Skip validation if value is None and field is optional
            if value is None:
                if field.required:
                    errors.append(
                        ValidationError(f"Required field '{name}' is None", name)
                    )
                continue
                
            # Validate field
            try:
                self._validate_field(field, value)
            except ValidationError as e:
                errors.append(e)
                
        return errors
        
    def _validate_field(self, field: FieldDefinition, value: Any) -> None:
        """Validate a single field."""
        # Type validation
        if field.validation_mode == ValidationMode.STRICT:
            if not self._validate_type_strict(field.field_type, value):
                raise ValidationError(
                    f"Invalid type for field '{field.name}'. "
                    f"Expected {field.field_type.value}",
                    field.name
                )
        else:
            try:
                # Try to coerce type if needed
                value = TypeConverter.convert(value, field.field_type, field.field_type)
            except ValueError as e:
                raise ValidationError(
                    f"Type conversion failed for field '{field.name}': {str(e)}",
                    field.name
                )
                
        # Constraint validation
        self._validate_constraints(field, value)
        
    def _validate_type_strict(self, field_type: FieldType, value: Any) -> bool:
        """Strictly validate type."""
        if field_type == FieldType.TEXT:
            return isinstance(value, str)
        elif field_type == FieldType.INTEGER:
            return isinstance(value, int)
        elif field_type == FieldType.FLOAT:
            return isinstance(value, float)
        elif field_type == FieldType.DECIMAL:
            return isinstance(value, (Decimal, str))
        elif field_type == FieldType.BOOLEAN:
            return isinstance(value, bool)
        elif field_type == FieldType.DATE:
            from datetime import date
            return isinstance(value, date)
        elif field_type == FieldType.TIMESTAMP:
            from datetime import datetime
            return isinstance(value, datetime)
        return True
        
    def _validate_constraints(self, field: FieldDefinition, value: Any) -> None:
        """Validate field constraints."""
        constraints = field.constraints
        
        # Text constraints
        if field.field_type == FieldType.TEXT:
            # Max length
            max_length = constraints.get("max_length")
            if max_length and len(str(value)) > max_length:
                raise ValidationError(
                    f"Text too long for field '{field.name}'. "
                    f"Maximum length is {max_length}",
                    field.name
                )
                
            # Format validation
            format_type = constraints.get("format")
            if format_type:
                import re
                if format_type == "email":
                    if not re.match(r"[^@]+@[^@]+\.[^@]+", str(value)):
                        raise ValidationError(
                            f"Invalid email format for field '{field.name}'",
                            field.name
                        )
                elif format_type == "phone":
                    if not re.match(r"^\+?[\d\s-]+$", str(value)):
                        raise ValidationError(
                            f"Invalid phone format for field '{field.name}'",
                            field.name
                        )
                        
            # Allowed values
            allowed_values = constraints.get("allowed_values")
            if allowed_values and value not in allowed_values:
                raise ValidationError(
                    f"Invalid value for field '{field.name}'. "
                    f"Must be one of: {', '.join(map(str, allowed_values))}",
                    field.name
                )
                
        # Numeric constraints
        elif field.field_type in [FieldType.INTEGER, FieldType.FLOAT, FieldType.DECIMAL]:
            # Convert to appropriate type for comparison
            if field.field_type == FieldType.DECIMAL:
                num_value = Decimal(str(value))
            else:
                num_value = float(value)
                
            # Min value
            min_value = constraints.get("min_value")
            if min_value is not None:
                if field.field_type == FieldType.DECIMAL:
                    min_value = Decimal(str(min_value))
                if num_value < min_value:
                    raise ValidationError(
                        f"Value too small for field '{field.name}'. "
                        f"Minimum value is {min_value}",
                        field.name
                    )
                    
            # Max value
            max_value = constraints.get("max_value")
            if max_value is not None:
                if field.field_type == FieldType.DECIMAL:
                    max_value = Decimal(str(max_value))
                if num_value > max_value:
                    raise ValidationError(
                        f"Value too large for field '{field.name}'. "
                        f"Maximum value is {max_value}",
                        field.name
                    )
                    
            # Precision for DECIMAL
            if field.field_type == FieldType.DECIMAL:
                precision = constraints.get("precision")
                if precision is not None:
                    decimal_places = abs(Decimal(str(value)).as_tuple().exponent)
                    if decimal_places > precision:
                        raise ValidationError(
                            f"Too many decimal places for field '{field.name}'. "
                            f"Maximum precision is {precision}",
                            field.name
                        )
