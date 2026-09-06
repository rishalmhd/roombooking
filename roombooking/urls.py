"""
URL configuration for roombooking project.

The `urlpatterns` list routes URLs to views.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


urlpatterns = [
    # Landing page → Customer Register
    path('', lambda request: redirect('/customer/register/')),

    path('admin/', admin.site.urls),

    # Manager URLs → /manager/register/
    path('manager/', include('manager_app.urls')),

    # Customer URLs → /customer/register/, /customer/login/, etc.
    path('customer/', include('customer_app.urls')),
]


# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )