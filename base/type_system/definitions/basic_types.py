# Basic types.
from type_system.core.types import define_type

# Basic types
define_type(type_name="String", base_type=str)
define_type(type_name="Integer", base_type=int)
define_type(type_name="Float", base_type=float)
define_type(type_name="Boolean", base_type=bool)
define_type(type_name="Date", base_type=str)  # Placeholder - replace with a proper date type if available
define_type(type_name="DateTime", base_type=str)  # Placeholder - replace with a proper datetime type

# Constrained types
define_type(
    type_name="PositiveInteger",
    base_type=int,
    parent_type="Integer",
    constraints={"min_value": 1},
    description="An integer that must be greater than zero."
)

define_type(
    type_name="PositiveFloat",
    base_type=float,
    parent_type="Float",
    constraints={"min_value": 0},
    description="A float that must be greater than or equal to zero."
)

# Basic types with validation
def is_valid_email(value):
    import re
    return re.fullmatch(r"[^@]+@[^@]+\.[^@]+", value) is not None

define_type(
    type_name="Email",
    base_type=str,
    parent_type="String",
    validation_rules=[is_valid_email],
    description="A valid email address."
)

def is_strong_password(value):
    return (len(value) >= 8 and
            any(c.islower() for c in value) and
            any(c.isupper() for c in value) and
            any(c.isdigit() for c in value))

define_type(
    type_name="StrongPassword",
    base_type=str,
    validation_rules=[is_strong_password],
    description="A password that is at least 8 characters long and contains at least one lowercase letter, one uppercase letter, and one digit."
)