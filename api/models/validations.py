from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

phoneValidation = RegexValidator(r'^\+?\d{10,15}$', 'Enter a valid phone number. Include the country code if necessary.')
ssnValidation = RegexValidator(r'^\d{9}$', 'The Social Insurance Number must be exactly 9 digits.')


def validate_duration(value):
    """"Check if the input is a digit and if it is less than or equal to 150"""
    if value > 150:
        raise ValidationError('Duration cannot be more than 150 minutes (2.5 hours).')


def validate_margin(value):
    if value > 100:
        raise ValidationError('Margin Percent cannot be biger than 100%')