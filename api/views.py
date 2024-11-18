from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.models.models import Service, Barber, BarberSchedule, Booking, TimeOffRequest
from .serializers import ServiceSerializer, BarberSerializer
from datetime import datetime, timedelta
from django.db.models import Q
from datetime import time

@api_view(['GET'])
def get_services(request):
    """Returns list of available services."""
    services = Service.objects.all()
    serializer = ServiceSerializer(services, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_qualified_barbers(request):
    """Returns list of qualified barbers for the provided service id."""
    service_id = request.query_params.get('service_id')
    if not service_id:
        return Response({"error": "Service ID is required."}, status=400)

    qualified_barbers = Barber.objects.filter(barberqualification__service_id=service_id)
    serializer = BarberSerializer(qualified_barbers, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_available_dates(request):
    """Returns list of available dates for the provided service id and barber id."""
    service_id = request.query_params.get('service_id')
    barber_id = request.query_params.get('barber_id')

    if not service_id or not barber_id:
        return Response({"error": "Service ID and Barber ID are required."}, status=400)

    # Fetch service duration
    service = Service.objects.get(id=service_id)
    duration = timedelta(minutes=service.duration)

    # Fetch barber's schedule
    schedules = BarberSchedule.objects.filter(barber_id=barber_id)

    # Fetch existing bookings and time off requests
    existing_bookings = Booking.objects.filter(barber_id=barber_id)
    time_off_requests = TimeOffRequest.objects.filter(barber_id=barber_id, isApproved=True)

    available_dates = []
    today = datetime.now().date()
    for schedule in schedules:
        weekday = schedule.day_of_week
        start_time = schedule.start_time
        end_time = schedule.end_time

        # Check availability for the next 30 days
        for i in range(30):
            date = today + timedelta(days=i)
            if date.strftime("%A") == weekday:
                # Ensure there is enough time for the service within working hours
                if (datetime.combine(date, end_time) - datetime.combine(date, start_time)) >= duration:
                    # Check for time off requests
                    if time_off_requests.filter(date=date).exists():
                        continue

                    # Check for existing bookings
                    if not existing_bookings.filter(booking_date=date).exists():
                        available_dates.append(date)

    return Response([date.strftime('%Y-%m-%d') for date in available_dates])

@api_view(['GET'])
def get_available_timeslots(request):
    """Returns list of available timeslots for the provided service id and barber id for the chosen date."""
    service_id = request.query_params.get('service_id')
    barber_id = request.query_params.get('barber_id')
    chosen_date = request.query_params.get('date')

    if not service_id or not barber_id or not chosen_date:
        return Response({"error": "Service ID, Barber ID, and Date are required."}, status=400)

    chosen_date = datetime.strptime(chosen_date, "%Y-%m-%d").date()
    service = Service.objects.get(id=service_id)
    duration = timedelta(minutes=service.duration)

    schedule = BarberSchedule.objects.filter(barber_id=barber_id, day_of_week=chosen_date.strftime("%A")).first()
    if not schedule:
        return Response({"error": "No schedule found for the barber on the chosen date."}, status=404)

    start_time = schedule.start_time
    end_time = schedule.end_time

    # Fetch existing bookings and time off requests
    existing_bookings = Booking.objects.filter(barber_id=barber_id, booking_date=chosen_date)
    time_off_requests = TimeOffRequest.objects.filter(barber_id=barber_id, date=chosen_date, isApproved=True)

    timeslot = start_time
    available_timeslots = []

    while timeslot < end_time:
        # Check if the timeslot is within a time off request
        if time_off_requests.filter(start_time__lte=timeslot, end_time__gte=timeslot).exists():
            timeslot = (datetime.combine(chosen_date, timeslot) + timedelta(minutes=15)).time()
            continue

        # Check if the timeslot overlaps with an existing booking
        overlap = False
        for booking in existing_bookings:
            booking_start = booking.start_time
            booking_end = (datetime.combine(chosen_date, booking_start) + duration).time()
            if booking_start <= timeslot < booking_end:
                overlap = True
                break

        if not overlap:
            available_timeslots.append(timeslot.strftime("%I:%M %p"))

        # Increment by 15 minutes
        timeslot = (datetime.combine(chosen_date, timeslot) + timedelta(minutes=15)).time()

    return Response(available_timeslots)
