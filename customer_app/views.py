from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.generic import View, ListView, DetailView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Avg
from datetime import datetime
import razorpay

from .forms import CustomerRegisterForm, LoginForm, ReviewForm
from .models import Room, Booking, Cart, User, Review


# -------------------------
# AUTH / REGISTRATION
# -------------------------
def register(request):
    form = CustomerRegisterForm()
    if request.method == "POST":
        form = CustomerRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = "customer"
            user.set_password(form.cleaned_data["password"])
            user.save()
            return redirect("customer_login")
    return render(request, "register.html", {"form": form})


def login_view(request):
    form = LoginForm()
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"]
            )
            if user:
                login(request, user)
                if user.role == "manager":
                    return redirect("/admin/")
                return redirect("home")
    return render(request, "login.html", {"form": form})


def customer_logout(request):
    logout(request)
    return redirect("customer_login")


# -------------------------
# HOME / ROOMS
# -------------------------
class HomeView(ListView):
    model = Room
    template_name = "home.html"
    context_object_name = "rooms"

    def get_queryset(self):
        qs = Room.objects.all()
        city = self.request.GET.get("city")
        start = self.request.GET.get("start")
        end = self.request.GET.get("end")

        if city:
            qs = qs.filter(city__icontains=city)

        if start and end:
            qs = qs.exclude(booking__start_date__lte=end, booking__end_date__gte=start)

        return qs


class RoomDetailView(DetailView):
    model = Room
    template_name = "room_detail.html"
    context_object_name = "room"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room = self.get_object()

        context["reviews"] = room.reviews.all().order_by('-created_at')
        context["avg_rating"] = (
            round(room.reviews.aggregate(Avg('rating'))['rating__avg'], 1)
            if room.reviews.exists()
            else None
        )

        if self.request.user.is_authenticated and self.request.user.role == "customer":
            existing = Review.objects.filter(user=self.request.user, room=room).first()
            if existing:
                context["reviewed"] = True
            else:
                context["review_form"] = ReviewForm()

        return context


# -------------------------
# CART
# -------------------------
@login_required
def add_to_cart(request, pk):
    room = Room.objects.get(id=pk)
    Cart.objects.create(user=request.user, room=room)
    return redirect("cart")


@login_required
def remove_from_cart(request, pk):
    cart_item = get_object_or_404(Cart, id=pk)
    cart_item.delete()
    return redirect("cart")


@login_required
def cart(request):
    items = Cart.objects.filter(user=request.user)
    total_price = sum(item.room.price for item in items)
    return render(request, "cart.html", {
        "cart_items": items,
        "total_price": total_price
    })


# -------------------------
# CHECKOUT → CREATE RAZORPAY ORDER
# -------------------------
@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items:
        return HttpResponse("Your cart is empty")

    total = sum(item.room.price for item in cart_items)
    amount_paise = int(total * 100)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    payment_order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": 1
    })

    request.session["rzp_order_id"] = payment_order["id"]

    return render(request, "payment_page.html", {
        "rzp_key_id": settings.RAZORPAY_KEY_ID,
        "rzp_order_id": payment_order["id"],
        "amount": amount_paise,
    })


# -------------------------
# PAYMENT VERIFY → CREATE BOOKINGS
# -------------------------
@method_decorator(csrf_exempt, name="dispatch")
class PaymentVerify(View):
    def post(self, request):

        print("PAYMENT RESPONSE =", request.POST)

        user = request.user
        cart_items = Cart.objects.filter(user=user)

        if not cart_items:
            return HttpResponse("Cart empty or session expired")

        for item in cart_items:
            Booking.objects.create(
                user=user,
                room=item.room,
                start_date=datetime.today(),
                end_date=datetime.today()
            )

        cart_items.delete()

        return redirect("checkout_done")


# -------------------------
# REVIEWS
# -------------------------
@login_required
def add_review(request, pk):
    room = Room.objects.get(id=pk)
    if Review.objects.filter(user=request.user, room=room).exists():
        return HttpResponse("You already reviewed this room.")

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.room = room
            review.save()
            return redirect("room_detail", pk=pk)

    return redirect("room_detail", pk=pk)


# -------------------------
# PASSWORD RESET
# -------------------------
def forgot_password(request):
    if request.method == "POST":
        email = request.POST["email"]
        mobile = request.POST["mobile"]
        try:
            user = User.objects.get(email=email, mobile=mobile)
            request.session["reset_user"] = user.id
            return redirect("reset_password")
        except User.DoesNotExist:
            return HttpResponse("Invalid details")
    return render(request, "forgot_password.html")


def reset_password(request):
    user_id = request.session.get("reset_user")
    if not user_id:
        return redirect("forgot_password")

    user = User.objects.get(id=user_id)

    if request.method == "POST":
        p1 = request.POST["password"]
        p2 = request.POST["confirm"]
        if p1 == p2:
            user.set_password(p1)
            user.save()
            return redirect("customer_login")
        else:
            return HttpResponse("Passwords mismatch")

    return render(request, "reset_password.html")


# -------------------------
# MY BOOKINGS
# -------------------------
@login_required
def booking_list(request):
    bookings = Booking.objects.filter(user=request.user)
    return render(request, "my_bookings.html", {"bookings": bookings})
