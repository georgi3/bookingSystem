from api.models.models import UserExtra, Barber, BarberQualification, BarberSchedule, TimeOffRequest, Booking, SelectedService
from api.formsets import SelectedServicesInlineFormset
from django.utils import timezone
from django.contrib import admin


class UserExtraInline(admin.StackedInline):
    model = UserExtra
    can_delete = False
    verbose_name = "Additional User Information"
    verbose_name_plural = "Additional User Information"


class BarberInline(admin.StackedInline):
    model = Barber
    can_delete = False
    verbose_name = "Barber Information"
    verbose_name_plural = "Barbers Information"


class BarberScheduleInline(admin.TabularInline):
    model = BarberSchedule
    can_delete = True
    extra = 1
    max_num = 7

    verbose_name = "Barber's Schedule"
    verbose_name_plural = "Barber's Schedule"


class BarberQualificationInline(admin.TabularInline):
    model = BarberQualification
    can_delete = True
    extra = 1

    verbose_name = "Barber's Qualification"
    verbose_name_plural = "Barber's Qualifications"


class TimeOffRequestInline(admin.TabularInline):
    model = TimeOffRequest
    can_delete = True
    extra = 0

    readonly_fields = ['date', 'start_time', 'end_time', 'reason', ]
    fields = ['date', 'start_time', 'end_time', 'reason', 'isApproved']

    verbose_name = "Upcoming Time Off Request"
    verbose_name_plural = "Upcoming Time Off Requests"

    def has_add_permission(self, request, obj=None):
        return False


class BookingInline(admin.TabularInline):
    model = Booking
    can_delete = True
    extra = 0
    readonly_fields = ['modify_booking_link', 'booking_date', 'start_time', 'status']
    fields = ['modify_booking_link', 'booking_date', 'start_time', 'status']

    def modify_booking_link(self, obj):
        from django.utils.html import format_html
        from django.urls import reverse
        return format_html(
            '<a href="{}">Modify Booking</a>',
            reverse('admin:api_booking_change', args=[obj.id]),
            obj.id
        )
    modify_booking_link.short_description = 'Booking'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(booking_date__gte=timezone.now().date())

    def has_add_permission(self, request, obj=None):
        return False

    verbose_name = "Upcoming Appointment"
    verbose_name_plural = "Upcoming Appointment"


class SelectedServicesInline(admin.TabularInline):
    model = SelectedService
    formset = SelectedServicesInlineFormset
    extra = 1
    min_num = 1

    verbose_name = "Selected Service"
    verbose_name_plural = "Selected Services"
