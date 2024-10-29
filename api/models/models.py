import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from datetime import time

from django.db.models import Sum, F, Q, Value
from django.db.models.functions import Concat

from api.models.validations import phoneValidation, ssnValidation, validate_duration, validate_margin
from .enums import ProvinceChoices, Weekday, BookingStatus


class UserExtra(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="User Account",
        help_text="The user associated with this customer information."
    )
    phone = models.CharField(
        max_length=12,
        validators=[phoneValidation],
        verbose_name="Phone Number",
        help_text="Enter the phone number with area code. Max 12 characters."
    )
    addressLine1 = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Address Line 1",
        help_text="Primary address line. E.g., street address or P.O. Box."
    )
    addressLine2 = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Address Line 2",
        help_text="Secondary address information. E.g., Apartment or suite number."
    )
    province = models.CharField(
        max_length=2,
        choices=ProvinceChoices.choices,
        default=ProvinceChoices.QUEBEC,
        blank=True,
        verbose_name="Province",
        help_text="Select the province or territory for this customer."
    )
    postal_code = models.CharField(
        max_length=6,
        blank=True,
        null=True,
        verbose_name="Postal Code",
        help_text="The postal code in 6-character format."
    )

    class Meta:
        verbose_name = "User Information"
        verbose_name_plural = "User Information"

    def __str__(self):
        return f"{self.user.username.capitalize()}'s Information"


class Barber(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="User Account",
        help_text="The user associated with this barber."
    )

    agreedMargin = models.PositiveIntegerField(
        verbose_name="Barber's Margin.",
        validators=[validate_margin],
        help_text='Margin a barber earns from their earnings.',
        default=60)

    socialInsuranceNumber = models.CharField(
        max_length=9,
        validators=[ssnValidation],
        verbose_name="Social Insurance Number (SIN)",
        help_text="Enter the 9-digit Social Insurance Number (SIN) without spaces or dashes.",
        blank=False,
        null=True
    )

    emergencyContactName = models.CharField(
        max_length=100,
        verbose_name="Emergency Contact Name",
        help_text="Enter the full name of the emergency contact.",
        blank=False,
        null=True
    )

    emergencyContactPhoneNumber = models.CharField(
        max_length=15,
        validators=[phoneValidation],
        verbose_name="Emergency Contact Phone Number",
        help_text="Enter a valid phone number for the emergency contact. Include country code if necessary.",
        blank=False,
        null=True
    )

    emergencyContactRelationship = models.CharField(
        max_length=100,
        verbose_name="Emergency Contact Relationship",
        help_text="Specify the relationship of the emergency contact to the barber (e.g., parent, sibling, friend).",
        blank=False,
        null=True
    )

    profileImage = models.ImageField(
        upload_to='profile_images/',
        verbose_name="Profile Image",
        help_text="Upload a profile image for the barber.",
        blank=True,
        null=True
    )

    def clean(self):
        """
        Ensure that the user associated with this Barber is marked as staff.
        """
        if not self.user.is_staff:
            raise ValidationError("The user must have staff status set to true, to be associated with a Barber.")

    class Meta:
        verbose_name = "Barber"
        verbose_name_plural = "Barbers"

    def __str__(self):
        return f"Barber {self.user.username.capitalize()}"

    @staticmethod
    def prepare_df_data(start_date: datetime.date, end_date: datetime.date):
        data = Booking.objects.filter(Q(booking_date__range=(start_date, end_date))).annotate(
            bookingId=F('id'),
            barberId=F('barber__id'),
            # barberName=Concat(F('barber__user__first_name'), Value(' '), F('barber__user__last_name')),
            barberName=F('barber__user__username'),
            barberMargin=F('barber__agreedMargin'),
            bookingDate=F('booking_date'),
            servicePrice=F('selectedservice__service__price'),
            serviceName=F('selectedservice__service__name')
        ).values('bookingId', 'barberId', 'barberName', 'barberMargin', 'bookingDate', 'servicePrice', 'serviceName')

        return list(data)


class Service(models.Model):
    name = models.CharField(max_length=255, verbose_name="Service Name")
    price = models.FloatField(verbose_name="Service Price")
    description = models.TextField(verbose_name="Service Description", blank=True, null=True)
    image = models.ImageField(upload_to='service_images/', blank=True, null=True, verbose_name="Service Image")
    duration = models.PositiveIntegerField(verbose_name="Service Duration", validators=[validate_duration], help_text='Enter Service Duration in Minutes')

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __str__(self):
        return self.name


class BarberQualification(models.Model):
    user = models.ForeignKey(
        Barber,
        on_delete=models.CASCADE,
        verbose_name="User Account",
        help_text="The barber associated with this qualification."
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name='Service Name')

    class Meta:
        verbose_name = "Barber Qualification"
        verbose_name_plural = "Barber Qualifications"
        constraints = [
            models.UniqueConstraint(fields=['user', 'service'], name='unique_barber_service')
        ]

    def __str__(self):
        return self.service.name


class BarberSchedule(models.Model):
    barber = models.ForeignKey(Barber, on_delete=models.CASCADE)
    day_of_week = models.CharField(max_length=20, choices=Weekday.choices)
    start_time = models.TimeField(default=time(9, 0))
    end_time = models.TimeField(default=time(17, 0))

    class Meta:
        unique_together = ('barber', 'day_of_week')

    def __str__(self):
        return ''


class TimeOffRequest(models.Model):
    barber = models.ForeignKey(Barber, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    reason = models.TextField(blank=True, null=True)
    isApproved = models.BooleanField(verbose_name='Is Approved', default=False, null=True)

    class Meta:
        unique_together = ('barber', 'date', 'start_time')
        verbose_name = 'Time Off Request'
        verbose_name_plural = 'Time Off Requests'

    def __str__(self):
        return f"Time Off Request for {self.date} from {self.start_time} to {self.end_time}."


class Booking(models.Model):
    barber = models.ForeignKey(Barber, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    booking_date = models.DateField()
    start_time = models.TimeField()
    status = models.CharField(max_length=20, choices=BookingStatus.choices, default=BookingStatus.PENDING)

    class Meta:
        verbose_name = 'Booking Appointment'
        verbose_name_plural = 'Booking Appointments'

    def __str__(self):
        return f"{self.barber}'s Appointment with {self.user}"


class SelectedService(models.Model):
    appointment = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        verbose_name="Booking Appointment",
        help_text="The appointment associated with the selected service."
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name='Service Name')

    class Meta:
        verbose_name = "Selected Service"
        verbose_name_plural = "Selected Services"
        constraints = [
            models.UniqueConstraint(fields=['appointment', 'service'], name='unique_appointment_service')
        ]

    def __str__(self):
        return f''
