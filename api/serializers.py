from rest_framework import serializers
# from api.models import Service
from api.models.models import Service, Barber, BarberQualification, BarberSchedule, Booking, SelectedService

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

class BarberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barber
        fields = ['id', 'user', 'agreedMargin']

class BarberQualificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarberQualification
        fields = '__all__'

class BarberScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarberSchedule
        fields = '__all__'
