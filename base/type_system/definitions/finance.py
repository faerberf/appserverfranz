# Finance-related types (e.g., Currency, Payment).
from type_system.core.types import define_type
from type_system.definitions.basic_types import PositiveFloat
# Currency Code
define_type(
    type_name="CurrencyCode",
    base_type=str,
    enum_values=["USD", "EUR", "JPY", "GBP", "CAD", "AUD", "CHF", "CNY", "SEK", "NZD"],
    description="Represents standard currency codes."
)

# Currency Value
define_type(
    type_name="CurrencyValue",
    base_type=dict,
    properties={
        "currency": "CurrencyCode",
        "amount": "PositiveFloat"
    },
    description="Represents an amount in a specific currency."
)