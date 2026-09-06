from django.shortcuts import render, redirect
from .forms import ManagerRegisterForm
from customer_app.models import User

def manager_register(request):
    form = ManagerRegisterForm()
    if request.method == "POST":
        form = ManagerRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = "manager"
            user.is_staff = True
            user.is_superuser = True
            user.set_password(form.cleaned_data["password"])
            user.save()
            return redirect("/admin/")
    return render(request, "manager_register.html", {"form": form})
