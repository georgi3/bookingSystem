from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet


class SelectedServicesInlineFormset(BaseInlineFormSet):
    def clean(self):
        super().clean()
        booking = self.instance
        barber = booking.barber
        qualified_services = barber.barberqualification_set.values_list('service', flat=True)

        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                selected_service = form.cleaned_data.get('service')

                if selected_service and selected_service.id not in qualified_services:
                    raise ValidationError(
                        f"The barber {barber.user.username} is not qualified for the service '{selected_service.name}'."
                    )
