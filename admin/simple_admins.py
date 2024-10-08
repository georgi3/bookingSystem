from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from admin.inlines import UserExtraInline, BarberInline, SelectedServicesInline
from api.models.models import Service, TimeOffRequest, Booking
from django.contrib.auth.models import User as UserDefaultModel


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


admin.site.unregister(UserDefaultModel)
admin.site.register(UserDefaultModel, CustomUserAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(TimeOffRequest, TimeOffRequestAdmin)
admin.site.register(Booking, BookingAdmin)

admin.site.site_header = "Number One Barbershop"
admin.site.site_title = "Number One Barbershop"
admin.site.index_title = "Number 1 Barbershop Admin"

