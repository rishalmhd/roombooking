from django.urls import path
from .views import manager_register

urlpatterns = [
    path('register/', manager_register, name="manager_register"),
]
