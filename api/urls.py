from django.urls import path
from api import views


urlpatterns = [
    path("services", views.get_services, name='services'),
    path('qualified-barbers', views.get_qualified_barbers, name='qualified-barbers'),
    path('available-dates', views.get_available_dates, name='available-dates'),
    path("available-time-slots", views.get_available_timeslots, name="available-time-slots"),
    # path("login", views.login, name="login"),
    # path("register", views.register, name="register"),
]