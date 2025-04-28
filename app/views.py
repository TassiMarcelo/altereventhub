import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Event, User, Ticket


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

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if id is None:
            Event.new(title, description, scheduled_at, request.user)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    return render(
        request,
        "app/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer},
    )


@login_required
def ticket_buy(request, eventId):
    user = request.user

    if request.method == "POST":
        quantity = request.POST.get("quantity")
        type = request.POST.get("type")

        # Chequear que esten todos los campos llenos
        if not all([quantity, type]):
            # Algún campo faltó
            print("Todos los campos son obligatorios.")

        # Chequear que quantity sea un entero positivo
        valError = "La cantidad debe ser un número entero positivo."
        try:
            if int(quantity) <= 0:
                raise ValueError(valError)
        except ValueError:
            print(valError)

        # Chequear que el tipo de ticket sea valido
        if type not in Ticket.Type.values:
            print("El tipo de ticket no es válido.")

        event = get_object_or_404(Event, pk=eventId)

        ticket = Ticket.new(
            buy_date=timezone.now(),
            quantity=quantity,
            type=type,
            event=event,
            user=user
        )

        print(f"Ticket comprado! Codigo: {str(ticket.ticket_code)}")

    return redirect("events")

def ticket_form(request, id):
    # Cuando intento acceder al ticket form (formulario de tarjeta de credito para comprar tickets), necesito saber si el evento existe
    event = get_object_or_404(Event, pk=id)
    return render(
        request,
        "app/ticket_form.html",
        {"event": event} # Pasar el contexto del evento a la parte del formulario de compra para que el usuario pueda ver que evento esta comprando, y para armar la solicitud de compra.
    )