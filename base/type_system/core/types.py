# Type model definitions and core functions.
import re
from core.errors import ValidationError
from core.events import trigger_event
from core.utils import resolve_node_definition, load_properties_from_external_source

type_registry = {}



def define_type(type_name, base_type, validation_rules=None, parent_type=None,
                properties=None, constraints=None, source=None, description=None,
                display_name=None, is_abstract=False, is_deprecated=False, version="1.0",
                tags=None, permissions=None, enum_values=None, is_nullable=False,
                is_structural=False):
    """
    Defines a new type and adds it to the type registry.
    """
    if type_name in type_registry:
        raise ValueError(f"Type '{type_name}' already exists.")

    if is_structural and not source:
        raise ValueError(f"'source' must be provided for structural type '{type_name}'.")

    if source:
      # structural type - load properties based on node definition
      properties = load_properties_from_external_source(source)

    type_model = {
        "type_name": type_name,
        "base_type": base_type,
        "validation_rules": validation_rules or [],
        "parent_type": parent_type,
        "properties": properties or {},
        "constraints": constraints or {},
        "source": source,
        "description": description,
        "display_name": display_name or type_name,
        "is_abstract": is_abstract,
        "is_deprecated": is_deprecated,
        "version": version,
        "tags": tags or [],
        "permissions": permissions or {},
        "enum_values": enum_values,
        "is_nullable": is_nullable,
        "is_structural": is_structural
    }

    # rest of the code same as before
    if parent_type:
        if parent_type.startswith("List[") and parent_type.endswith("]"):
            # Extract the inner type
            list_item_type = parent_type[5:-1]

            # Add a validation rule to check all items in the list
            def list_validation_rule(values):
                for item in values:
                    validate(item, list_item_type)
                return True

            type_model["validation_rules"].append(list_validation_rule)
        elif parent_type.startswith("Dictionary[") and parent_type.endswith("]"):
            # Extract key and value types
            key_type, value_type = parent_type[11:-1].split(",")
            key_type = key_type.strip()
            value_type = value_type.strip()
             # Add a validation rule to check all keys and values in the dictionary
            def dict_validation_rule(value):
                for k, v in value.items():
                    validate(k, key_type)
                    validate(v, value_type)
                return True

            type_model["validation_rules"].append(dict_validation_rule)
        elif parent_type.startswith("Nullable[") or parent_type.startswith("Optional["):
            type_model["is_nullable"] = True
            # Extract the inner type and proceed as before.
            parent_type = parent_type[9:-1] if parent_type.startswith("Nullable") else parent_type[9:-1]
            parent_model = get_type(parent_type)

            if parent_model:
              # Inherit validation rules, properties, and constraints.
              type_model["validation_rules"].extend(parent_model["validation_rules"])
              type_model["properties"] = {**parent_model["properties"], **type_model["properties"]}

              # Inherit constraints, but allow child type to override
              inherited_constraints = {k: v for k, v in parent_model["constraints"].items() if k not in type_model["constraints"]}
              type_model["constraints"].update(inherited_constraints)
            else:
              raise ValueError(f"Parent type '{parent_type}' not found.")
        else:
            parent_model = get_type(parent_type)
            if parent_model:
                # Inherit validation rules, properties, and constraints.
                type_model["validation_rules"].extend(parent_model["validation_rules"])
                type_model["properties"] = {**parent_model["properties"], **type_model["properties"]}

                # Inherit constraints, but allow child type to override
                inherited_constraints = {k: v for k, v in parent_model["constraints"].items() if k not in type_model["constraints"]}
                type_model["constraints"].update(inherited_constraints)

            else:
                raise ValueError(f"Parent type '{parent_type}' not found.")

    type_registry[type_name] = type_model

    trigger_event("on_type_defined", {"type_model": type_model})

    return type_model


def get_type(type_name):
    """
    Retrieves a type model by its name.
    """
    type_model = type_registry.get(type_name)
    if not type_model:
        raise ValueError(f"Type '{type_name}' not found.")
    return type_model

def validate(value, type_name, context=None):
    """
    Validates a value against a type definition.
    """
    type_model = get_type(type_name)

    # Check for nullability
    if value is None:
        if type_model["is_nullable"]:
            return value  # None is allowed
        else:
            raise ValidationError(f"Value cannot be None for type {type_name}", error_code="NULL_VALUE", type_name=type_name)

    if not isinstance(value, type_model["base_type"]):
        raise ValidationError(
            f"Value '{value}' is not of type {type_model['base_type'].__name__} (expected {type_name})",
            error_code="TYPE_MISMATCH",
            value=value,
            type_name=type_name,
        )

    # Handle enumerated types
    if type_model["enum_values"] and value not in type_model["enum_values"]:
        raise ValidationError(
            f"Value '{value}' is not a valid enum value for type {type_name} (allowed values: {type_model['enum_values']})",
            error_code="INVALID_ENUM_VALUE",
            value=value,
            type_name=type_name,
        )

    for rule in type_model["validation_rules"]:
        if not rule(value):
            raise ValidationError(
                f"Value '{value}' failed validation rule {rule.__name__} for type {type_name}",
                error_code="VALIDATION_RULE_FAILED",
                value=value,
                type_name=type_name,
            )

    if type_model["constraints"]:
        for constraint_name, constraint_value in type_model["constraints"].items():
            if constraint_name == "min_value" and value < constraint_value:
                raise ValidationError(
                    f"Value '{value}' is less than minimum value {constraint_value} for type {type_name}",
                    error_code="MIN_VALUE_VIOLATION",
                    value=value,
                    type_name=type_name,
                )
            if constraint_name == "max_value" and value > constraint_value:
                raise ValidationError(
                    f"Value '{value}' is greater than maximum value {constraint_value} for type {type_name}",
                    error_code="MAX_VALUE_VIOLATION",
                    value=value,
                    type_name=type_name,
                )
            if constraint_name == "pattern" and not re.fullmatch(constraint_value, value):
                raise ValidationError(
                    f"Value '{value}' does not match pattern '{constraint_value}' for type {type_name}",
                    error_code="PATTERN_MISMATCH",
                    value=value,
                    type_name=type_name,
                )
            if constraint_name == "unique":
                # Implement logic to check for uniqueness
                pass

            if constraint_name == "allowed_values" and value not in constraint_value:
                raise ValidationError(
                    f"Value '{value}' is not in the allowed values list for type {type_name}",
                    error_code="ALLOWED_VALUES_VIOLATION",
                    value=value,
                    type_name=type_name
                )

    if type_model["properties"]:  # Composite type
        if not isinstance(value, dict):
            raise ValidationError(
                f"Value '{value}' is not a dict for composite type {type_name}",
                error_code="TYPE_MISMATCH",
                value=value,
                type_name=type_name,
            )
        for prop_name, prop_type_name in type_model["properties"].items():
            if prop_name not in value:
                raise ValidationError(
                    f"Missing property '{prop_name}' in value '{value}' for type {type_name}",
                    error_code="MISSING_PROPERTY",
                    field=prop_name,
                    value=value,
                    type_name=type_name,
                )
            validate(value[prop_name], prop_type_name, context)  # Recursive validation

    trigger_event("on_validation_success", {"value": value, "type_name": type_name, "context": context})

    return value

def define_type_alias(alias_name, target_type):
    """
    Defines a type alias.
    """
    if alias_name in type_registry:
        raise ValueError(f"Type or alias '{alias_name}' already exists.")
    if target_type not in type_registry:
        raise ValueError(f"Target type '{target_type}' not found.")

    type_registry[alias_name] = get_type(target_type)

def map_type(type_name):
    """
    Decorator to map a Python class to a custom type.
    """
    def decorator(cls):
        # Add a _type_name attribute to the class for later reference
        cls._type_name = type_name
        return cls
    return decorator

def validate_type(func):
    """
    Decorator to automatically validate method arguments and return value against their defined types.
    """
    def wrapper(*args, **kwargs):
        import inspect
        bound_arguments = inspect.signature(func).bind(*args, **kwargs)
        bound_arguments.apply_defaults()

        # Validate arguments
        for arg_name, arg_value in bound_arguments.arguments.items():
            if arg_name != 'self' and arg_name in func.__annotations__:
                arg_type = func.__annotations__[arg_name]
                if isinstance(arg_type, str):
                    # Handle forward references (types defined as strings)
                    import __main__
                    arg_type = eval(arg_type, vars(__main__))
                if hasattr(arg_type, '_type_name'):
                    validate(arg_value, arg_type._type_name)

        # Call the original function
        result = func(*args, **kwargs)

        # Validate return value
        if 'return' in func.__annotations__:
            return_type = func.__annotations__['return']
            if isinstance(return_type, str):
                import __main__
                return_type = eval(return_type, vars(__main__))
            if hasattr(return_type, '_type_name'):
                validate(result, return_type._type_name)

        return result
    return wrapper