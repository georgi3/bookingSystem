from django.utils import timezone

from api.models.enums import BookingStatus
from django.db.models import Q
from api.models.models import Booking, Barber
from django.contrib import admin
from .inlines import BookingInline, TimeOffRequestInline, BarberQualificationInline, BarberScheduleInline


class BarberAdmin(admin.ModelAdmin):
    inlines = [BookingInline, TimeOffRequestInline, BarberQualificationInline, BarberScheduleInline]
    list_display = ('user', 'get_appointments_count_today', 'get_expected_earnings_today')
    search_fields = ('user__username', 'socialInsuranceNumber')
    list_filter = ('user',)

    readonly_fields = ('user',)
    fields = ('user',)

    change_list_template = "admin/barber_change_list.html"

    def get_appointments_today(self, obj):
        """
        Returns the number of appointments the barber has today.
        """
        today = timezone.now().date()
        appointments = Booking.objects.filter(
            Q(status=BookingStatus.CONFIRMED) | Q(status=BookingStatus.COMPLETED),
            barber=obj,
            booking_date=today)
        return appointments

    def get_appointments_count_today(self, obj):
        return self.get_appointments_today(obj).count()

    def get_expected_earnings_today(self, obj):
        """Returns Expected Earnings Today, for confirmed and completed bookings"""
        appointments = self.get_appointments_today(obj)
        earnings = 0
        for appointment in appointments:
            selected_services = appointment.selectedservice_set.all()
            if selected_services.exists():
                for service in selected_services:
                    earnings += service.service.price
        return f'${earnings:.2f}'

    def get_total_earnings(self, start_date, end_date):
        """
        Helper function to calculate total earnings between two dates.
        """
        appointments = Booking.objects.filter(
            Q(status=BookingStatus.CONFIRMED) | Q(status=BookingStatus.COMPLETED),
            booking_date__range=(start_date, end_date)
        ).prefetch_related('selectedservice_set__service')

        total_earnings = 0
        for appointment in appointments:
            for service in appointment.selectedservice_set.all():
                total_earnings += service.service.price

        return total_earnings

    def get_report_data(self, start_date=None, end_date=None):
        """
        Calculate earnings based on the date range.
        Default date range is today.
        """
        today = timezone.now().date()
        if not start_date:
            start_date = today
        if not end_date:
            end_date = today

        earnings_total = self.get_total_earnings(start_date, end_date)
        earnings_after_margin = earnings_total * 0.6  # 60% margin

        return {
            'earnings_total': earnings_total,
            'earnings_after_margin': earnings_after_margin,
            'start_date': start_date,
            'end_date': end_date
        }

    def changelist_view(self, request, extra_context=None):
        # If the form is submitted via GET, process GET data
        print("Entering changelist_view")
        print("Request method:", request.method)
        print("GET parameters:", request.GET)

        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        # Default to today's date if no dates are provided
        if not start_date:
            start_date = timezone.now().date()
        if not end_date:
            end_date = timezone.now().date()

        # Parse the dates
        try:
            if isinstance(start_date, str):
                start_date = timezone.datetime.strptime(start_date, "%Y-%m-%d").date()
            if isinstance(end_date, str):
                end_date = timezone.datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            start_date = end_date = timezone.now().date()

        # Get the report data
        report_data = self.get_report_data(start_date, end_date)

        # Pass the report data to the template
        extra_context = extra_context or {}
        extra_context['report_data'] = report_data
        extra_context['start_date'] = start_date
        extra_context['end_date'] = end_date

        print("Returning from changelist_view with report data")
        return super().changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request):
        return False

    get_appointments_count_today.short_description = "Appointments Today"
    get_expected_earnings_today.short_description = "Expected Earnings Today"


admin.site.register(Barber, BarberAdmin)