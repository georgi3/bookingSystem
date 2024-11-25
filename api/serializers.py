from time import process_time_ns

from rest_framework import serializers
# from api.models import Service
from api.models.models import Service, Barber, BarberQualification, BarberSchedule, Booking, SelectedService

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

class BarberSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    profile_image = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Barber
        fields = ['id', 'name', 'profile_image', 'position']

    def get_name(self, obj):
        return f"{obj.user.username}"

    def get_profile_image(self, obj):
        request = self.context.get('request')
        try:
            data = request.build_absolute_uri(obj.profileImage.url)
        except Exception as e:
            data = None
        return data


class BarberScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarberSchedule
        fields = '__all__'
