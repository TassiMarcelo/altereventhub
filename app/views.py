import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages
from .models import Comment, Event
from .forms import CommentForm

from .models import Event, User, Ticket, RefundRequest


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
#crear comentario
@login_required
def add_comment(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.event = event
            comment.save()
            messages.success(request, '¡Comentario publicado!')
            return redirect('event_detail', id=event.id)
    else:
        form = CommentForm()
    return render(request, 'comments/add_comment.html', {'form': form, 'event': event})

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, user=request.user)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Comentario actualizado!')
            return redirect('event_detail', id=comment.event.id)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'comments/edit_comment.html', {'form': form, 'comment': comment})



@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user != comment.user and request.user != comment.event.organizer:
        return HttpResponseForbidden()

    comment.delete()

    # Redirigir a la URL indicada en 'next', si existe
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    
    # Si no hay 'next', redirigir al detalle del evento como fallback
    return redirect('event_detail', id=comment.event.id)


@login_required
def organizer_comments(request):
    if not request.user.is_organizer:
        return redirect('events')
    
    # Obtener solo los eventos creados por este organizador
    organizer_events = Event.objects.filter(organizer=request.user)
    
    # Obtener todos los comentarios de esos eventos
    comments = Comment.objects.filter(event__in=organizer_events).select_related('user', 'event').order_by('-created_at')
    
    return render(request, 'comments/organizer_comments.html', {
        'comments': comments
    })
    
    
def view_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    return render(request, 'comments/view_comment.html', {'comment': comment})
def solicitar_reembolso(request):
    return render(request, 'request_form.html')
@login_required
def solicitar_reembolso(request):
    if request.method == "POST":
        ticket_code = request.POST.get("ticket_code")
        reason = request.POST.get("reason")     
        details = request.POST.get("details")   
       
        if not ticket_code or not reason:
            context = {
                "errors": "Por favor completá los campos.",
                "ticket_code": ticket_code,
                "reason": reason,
                "details": details,
            }
            return render(request, "request_form.html", context)

        refund_request = RefundRequest.objects.create(
            ticket_code=ticket_code,
            reason=reason,
            details=details,
            requester=request.user
        )
        print(f"Se ha guardado un nuevo reembolso: {refund_request.ticket_code}, {refund_request.reason}, {refund_request.details}, {refund_request.requester}")

        return redirect("events")


    return render(request, "request_form.html")
