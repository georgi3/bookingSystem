from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.models.models import Service, Barber, BarberSchedule, Booking, TimeOffRequest, SelectedService
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
    serializer = BarberSerializer(qualified_barbers, many=True, context={'request': request})
    return Response(serializer.data)


def get_time_slots(barber_id, date, service_id):
    """
    Generate a list of time slots for a barber on a given date, considering service duration,
    existing appointments, time-off requests, and excluding past slots for the current day.

    Args:
        barber_id (int): ID of the barber.
        date (datetime.date): Date for which to generate the slots.
        service_id (int): ID of the service to calculate the duration.

    Returns:
        list: List of time objects representing 15-minute intervals.
    """
    try:
        # Return an empty list if the date is in the past
        now = datetime.now()
        if date < now.date():
            return []

        # Get the barber's schedule for the specified day of the week
        day_of_week = date.strftime('%A')
        schedule = BarberSchedule.objects.get(barber_id=barber_id, day_of_week=day_of_week)

        # Get the duration of the service
        service = Service.objects.get(id=service_id)
        service_duration = timedelta(minutes=service.duration)

        start_time = schedule.start_time
        end_time = schedule.end_time

        # Adjust end time for the service duration
        adjusted_end_time = (datetime.combine(date, end_time) - service_duration).time()

        # Fetch existing appointments and time-off requests for the barber on the given date
        appointments = Booking.objects.filter(barber_id=barber_id, booking_date=date)
        time_offs = TimeOffRequest.objects.filter(barber_id=barber_id, date=date, isApproved=True)

        # Calculate blocked times based on existing appointments
        blocked_intervals = []
        for appointment in appointments:
            selected_services = SelectedService.objects.filter(appointment=appointment)
            total_duration = sum([s.service.duration for s in selected_services], 0)
            total_duration_delta = timedelta(minutes=total_duration)

            appointment_start = datetime.combine(date, appointment.start_time)
            appointment_end = appointment_start + total_duration_delta
            adjusted_start_time = appointment_start - service_duration

            blocked_intervals.append((adjusted_start_time.time(), appointment_end.time()))

        # Calculate blocked times based on time-off requests
        for time_off in time_offs:
            to_start_time = time_off.start_time
            to_end_time = time_off.end_time
            to_start_dt = datetime.combine(date, to_start_time) - service_duration
            to_end_dt = datetime.combine(date, to_end_time)
            blocked_intervals.append((to_start_dt.time(), to_end_dt.time()))

        # Generate time slots at 15-minute intervals, excluding blocked intervals
        slots = []
        current_time = datetime.combine(date, start_time)
        end_datetime = datetime.combine(date, adjusted_end_time)

        # Ensure we exclude past time slots for today
        while current_time <= end_datetime:
            slot_time = current_time.time()
            if date == now.date() and current_time.time() <= now.time():
                current_time += timedelta(minutes=15)
                continue

            # Check if the slot is not in any blocked interval
            if not any(start <= slot_time < end for start, end in blocked_intervals):
                slots.append(slot_time)
            current_time += timedelta(minutes=15)

        return slots

    except BarberSchedule.DoesNotExist:
        print('Schedule not found for the barber on this day.')
        return []

    except Service.DoesNotExist:
        print('Service not found.')
        return []

    except Exception as e:
        print(f"Error generating time slots: {e}")
        return []


@api_view(['GET'])
def get_blocked_dates(request):
    """
    Returns a list of dates that are fully booked or unavailable for a given barber.
    """
    barber_id = request.query_params.get('barber_id')

    if not barber_id:
        return Response({"error": "Barber ID is required."}, status=400)

    today = datetime.now().date()

    # Fetch bookings and time-off requests starting from today
    bookings = Booking.objects.filter(barber_id=barber_id, booking_date__gte=today)
    time_off_requests = TimeOffRequest.objects.filter(barber_id=barber_id, date__gte=today, isApproved=True)

    # Identify dates with full bookings or time-off requests
    busy_dates = set()

    for booking in bookings:
        busy_dates.add(booking.booking_date)

    for time_off in time_off_requests:
        busy_dates.add(time_off.date)

    blocked_dates = []
    for busy_date in busy_dates:
        print(busy_date)
        time_slots = get_time_slots(barber_id, busy_date, barber_id)
        print(time_slots)
        if len(time_slots) == 0:
            blocked_dates.append(busy_date)

    # Return sorted blocked dates
    return Response(sorted([date.strftime('%Y-%m-%d') for date in blocked_dates]))


@api_view(['GET'])
def get_available_timeslots(request):
    """
    Retrieve available time slots for a specific barber on a specific date.
    """
    try:
        barber_id = request.query_params.get('barber_id')
        date = request.query_params.get('date')
        service_id = request.query_params.get('service_id')

        if not barber_id or not date or not service_id:
            return Response({"error": "barber_id, date, service_id are required parameters"}, status=400)

        date = datetime.strptime(date, '%Y-%m-%d').date()
        slots = get_time_slots(barber_id, date, service_id)
        return Response(slots, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)



# def get_available_timeslots(request):
#     """Returns list of available timeslots for the provided service id and barber id for the chosen date."""
#     service_id = request.query_params.get('service_id')
#     barber_id = request.query_params.get('barber_id')
#     chosen_date = request.query_params.get('date')
#
#     if not service_id or not barber_id or not chosen_date:
#         return Response({"error": "Service ID, Barber ID, and Date are required."}, status=400)
#
#     chosen_date = datetime.strptime(chosen_date, "%Y-%m-%d").date()
#     service = Service.objects.get(id=service_id)
#     duration = timedelta(minutes=service.duration)
#
#     schedule = BarberSchedule.objects.filter(barber_id=barber_id, day_of_week=chosen_date.strftime("%A")).first()
#     if not schedule:
#         return Response({"error": "No schedule found for the barber on the chosen date."}, status=404)
#
#     start_time = schedule.start_time
#     end_time = schedule.end_time
#
#     # Fetch existing bookings and time off requests
#     existing_bookings = Booking.objects.filter(barber_id=barber_id, booking_date=chosen_date)
#     time_off_requests = TimeOffRequest.objects.filter(barber_id=barber_id, date=chosen_date, isApproved=True)
#
#     timeslot = start_time
#     available_timeslots = []
#
#     while timeslot < end_time:
#         # Check if the timeslot is within a time off request
#         if time_off_requests.filter(start_time__lte=timeslot, end_time__gte=timeslot).exists():
#             timeslot = (datetime.combine(chosen_date, timeslot) + timedelta(minutes=15)).time()
#             continue
#
#         # Check if the timeslot overlaps with an existing booking
#         overlap = False
#         for booking in existing_bookings:
#             booking_start = booking.start_time
#             booking_end = (datetime.combine(chosen_date, booking_start) + duration).time()
#             if booking_start <= timeslot < booking_end:
#                 overlap = True
#                 break
#
#         if not overlap:
#             available_timeslots.append(timeslot.strftime("%I:%M %p"))
#
#         # Increment by 15 minutes
#         timeslot = (datetime.combine(chosen_date, timeslot) + timedelta(minutes=15)).time()
#
#     return Response(available_timeslots)
