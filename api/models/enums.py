from django.db import models


class ProvinceChoices(models.TextChoices):
    ALBERTA = "AB", "Alberta"
    BRITISH_COLUMBIA = "BC", "British Columbia"
    MANITOBA = "MB", "Manitoba"
    NEW_BRUNSWICK = "NB", "New Brunswick"
    NEWFOUNDLAND_AND_LABRADOR = "NL", "Newfoundland and Labrador"
    NOVA_SCOTIA = "NS", "Nova Scotia"
    ONTARIO = "ON", "Ontario"
    PRINCE_EDWARD_ISLAND = "PE", "Prince Edward Island"
    QUEBEC = "QC", "Quebec"
    SASKATCHEWAN = "SK", "Saskatchewan"
    NORTHWEST_TERRITORIES = "NT", "Northwest Territories"
    NUNAVUT = "NU", "Nunavut"
    YUKON = "YT", "Yukon"


class Weekday(models.TextChoices):
    MONDAY = 'Monday', 'Monday'
    TUESDAY = 'Tuesday', 'Tuesday'
    WEDNESDAY = 'Wednesday', 'Wednesday'
    THURSDAY = 'Thursday', 'Thursday'
    FRIDAY = 'Friday', 'Friday'
    SATURDAY = 'Saturday', 'Saturday'
    SUNDAY = 'Sunday', 'Sunday'


class BookingStatus(models.TextChoices):
    NO_SHOW = 'noShow', 'No Show'
    CANCELLED = 'cancelled', 'Cancelled'
    CONFIRMED = 'confirmed', 'Confirmed'
    COMPLETED = 'completed', 'Completed'
    PENDING = 'pending', 'Pending'
