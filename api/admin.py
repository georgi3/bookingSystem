import datetime

from django.contrib.auth.admin import UserAdmin
from datetime import timedelta
from api.models.enums import BookingStatus
from django.db.models import Q
from api.models.models import UserExtra, Barber, BarberQualification, BarberSchedule, TimeOffRequest, Booking, \
    SelectedService, Service
from api.formsets import SelectedServicesInlineFormset
from django.utils import timezone
from django.contrib import admin
from django.contrib.auth.models import User as UserDefaultModel
import pandas as pd


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


class CustomUserAdmin(UserAdmin):
    inlines = (UserExtraInline, BarberInline)
    list_display = ['username', 'is_barber',  'is_staff']

    def is_barber(self, obj):
        is_barber = obj.barber
        if is_barber:
            return 'Barber'
        return '-'

    def get_inline_instances(self, request, obj=None):
        if obj:  # Only show inlines for existing users
            return super().get_inline_instances(request, obj)
        return []

    is_barber.short_description = 'Is Barber'


class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "formatted_duration")

    def formatted_duration(self, obj):
        """
        Custom method to display the duration in HH:MM format, removing seconds.
        """
        total_minutes = int(obj.duration)
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours}h {minutes}min"

    formatted_duration.short_description = 'Duration'


class TimeOffRequestAdmin(admin.ModelAdmin):
    list_display = ['barber', 'date', 'start_time', 'end_time']

    fields = ['date', 'start_time', 'end_time', 'reason']
    # TODO: only superuser* manager should see it

    def get_queryset(self, request):
        """
        Restrict the displayed time-off requests to the logged-in barber's own requests.
        """
        qs = super().get_queryset(request)
        # If the logged-in user is a barber, only show their own time-off requests
        if request.user.is_staff and hasattr(request.user, 'barber'):
            return qs.filter(barber__user=request.user)
        return qs

    def save_model(self, request, obj, form, change):
        """
        Ensure that barbers can only create time-off requests for themselves.
        """
        if request.user.is_staff and hasattr(request.user, 'barber'):
            obj.barber = request.user.barber
        super().save_model(request, obj, form, change)


class BookingAdmin(admin.ModelAdmin):
    inlines = [SelectedServicesInline]
    list_display = ['barber', 'booking_date', 'start_time', 'status']
    list_editable = ['status']


import plotly.graph_objs as go
from plotly.offline import plot


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
        df = pd.DataFrame(Barber.prepare_df_data(start_date, end_date))
        # earnings_total = self.get_total_earnings(start_date, end_date)
        # print(df)
        df['barberCut'] = df['servicePrice'] * df['barberMargin'] / 100
        df['shopCut'] = df['servicePrice'] * (100 - df['barberMargin']) / 100

        earnings_total = df['servicePrice'].sum()
        earnings_after_margin = df['shopCut'].sum()

        traces = []
        total_earnings = df.groupby('bookingDate')['servicePrice'].sum()
        trace = go.Scatter(x=total_earnings.index, y=total_earnings.values, mode='lines', name='Total')
        traces.append(trace)
        for barber in df['barberName'].unique():
            barberDf = df[df['barberName'] == barber]
            barber_earnings = barberDf.groupby('bookingDate')['servicePrice'].sum()
            trace = go.Scatter(x=barber_earnings.index, y=barber_earnings.values, mode='lines', name=barber)
            traces.append(trace)
        layout = go.Layout(
            title='Projected Earnings Per Day',
            xaxis=dict(title='Date'),
            yaxis=dict(title='Earnings'),
        )
        fig = go.Figure(data=traces, layout=layout)
        return {
            'earnings_total': earnings_total,
            'earnings_after_margin': earnings_after_margin,
            'plot_div': fig.to_html()
        }

    def changelist_view(self, request, extra_context=None):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if not start_date:
            start_date = timezone.now().date()
        if not end_date:
            end_date = timezone.now().date() + timedelta(days=7)

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

        # Prevents from redirect due to not whitelisted params
        mutable_get = request.GET.copy()
        mutable_get.pop('start_date', None)
        mutable_get.pop('end_date', None)
        request.GET = mutable_get

        return super().changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request):
        return False

    get_appointments_count_today.short_description = "Appointments Today"
    get_expected_earnings_today.short_description = "Expected Earnings Today"


admin.site.register(Barber, BarberAdmin)

admin.site.unregister(UserDefaultModel)
admin.site.register(UserDefaultModel, CustomUserAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(TimeOffRequest, TimeOffRequestAdmin)
admin.site.register(Booking, BookingAdmin)

admin.site.site_header = "Number One Barbershop"
admin.site.site_title = "Number One Barbershop"
admin.site.index_title = "Number 1 Barbershop Admin"
