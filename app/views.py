import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Event, User,Category
from django.db.models import Count


def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        is_organizer = request.POST.get("is-organizer") is not None
        password = request.POST.get("password")
        password_confirm = request.POST.get("password-confirm")

        errors = User.validate_new_user(email, username, password, password_confirm)

        if len(errors) > 0:
            return render(
                request,
                "accounts/register.html",
                {
                    "errors": errors,
                    "data": request.POST,
                },
            )
        else:
            user = User.objects.create_user(
                email=email, username=username, password=password, is_organizer=is_organizer
            )
            login(request, user)
            return redirect("events")

    return render(request, "accounts/register.html", {})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(
                request, "accounts/login.html", {"error": "Usuario o contraseña incorrectos"}
            )

        login(request, user)
        return redirect("events")

    return render(request, "accounts/login.html")


def home(request):
    return render(request, "home.html")


@login_required
def events(request):
    events = Event.objects.all().order_by("scheduled_at")
    return render(
        request,
        "app/events.html",
        {"events": events, "user_is_organizer": request.user.is_organizer},
    )


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    return render(request, "app/event_detail.html", {"event": event})


@login_required
def event_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        event = get_object_or_404(Event, pk=id)
        event.delete()
        return redirect("events")

    return redirect("events")


@login_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")
    
    categories = Category.objects.filter(is_active=True)
    selected_categories = []

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")
        category_ids = request.POST.getlist("categories")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        selected_categories = Category.objects.filter(id__in=category_ids)

        if id is None:
            Event.new(title, description, scheduled_at, request.user, selected_categories)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user, selected_categories)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)
        selected_categories = event.categories.values_list("id", flat=True)

    return render(
        request,
        "app/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer, "categories": categories, "selected_categories": selected_categories},
    )

@login_required
def category_list(request):
    categories = Category.objects.annotate(event_count=Count("events"))
    return render(request, "app/category_list.html", {"categories": categories})
                  
@login_required
def category_form(request, id=None):
    
    if not request.user.is_organizer:
        return redirect("category_list")
    
    category =None
    if id:
        category = get_object_or_404(Category, pk=id)

    if request.method =="POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description","")
        is_active = request.POST.get("is_active") == "on"

        if category:
            category.name = name
            category.description = description
            category. is_active = is_active
        else:
            category = Category(name=name, description=description, is_active=is_active)
        try:
            category.clean()
            category.save()
            return redirect("category_list")
        except ValidationError as e:
            return render(
                request,
                "app/category_form.html",
             {
                 "category": category,
                 "error": e.message_dict
             },
            )

    return render( request, "app/category_form.html", {"category": category})

@login_required
def category_delete(request, id):
    if not request.user.is_organizer:
        return redirect("category_list")
    
    category = get_object_or_404(Category, pk=id)
    category.delete()
    return redirect("category_list")

def category_events(request, id):
    category = get_object_or_404(Category, id=id)
    events= category.events.all()
    return render(request, "app/category_events-html",{"category": category, "events":events})
