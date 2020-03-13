from django.core.exceptions import ValidationError
from decimal import Decimal

# Custom validators for Inventory

def validate_udffield_decimal(value):
    try:
        value = Decimal(value)
        return value
    except:
        raise ValidationError("This field must be a Decimal")
