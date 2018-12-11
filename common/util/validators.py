from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

def validate_trim_whitespace(value):
    return value.strip()
