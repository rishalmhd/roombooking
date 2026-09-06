from django.urls import path
from django.shortcuts import render

from .views import (
    register, login_view, HomeView, RoomDetailView, add_to_cart, cart,
    checkout, add_review, forgot_password, reset_password,
    booking_list, remove_from_cart, customer_logout,
    PaymentVerify
)

urlpatterns = [
    # Home page
    path('home/', HomeView.as_view(), name="home"),

    # Auth
    path('register/', register, name="customer_register"),
    path('login/', login_view, name="customer_login"),
    path('logout/', customer_logout, name="logout"),

    # Rooms
    path('room/<int:pk>/', RoomDetailView.as_view(), name="room_detail"),

    # Cart
    path('add-to-cart/<int:pk>/', add_to_cart, name="add_to_cart"),
    path('remove-from-cart/<int:pk>/', remove_from_cart, name="remove_from_cart"),
    path('cart/', cart, name="cart"),

    # Checkout & Razorpay
    path('checkout/', checkout, name="checkout"),
    path('payment/verify/', PaymentVerify.as_view(), name="payment_verify"),

    # Payment success page
    path(
        'checkout/done/',
        lambda request: render(request, "checkout_done.html"),
        name="checkout_done"
    ),

    # Reviews
    path('room/<int:pk>/review/', add_review, name="add_review"),

    # Password reset
    path('forgot-password/', forgot_password, name="forgot_password"),
    path('reset-password/', reset_password, name="reset_password"),

    # Bookings
    path('my-bookings/', booking_list, name="booking_list"),
]
