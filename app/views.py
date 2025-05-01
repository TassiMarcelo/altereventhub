import datetime
from django.contrib.auth import authenticate, login
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages
from .models import Comment, Event
from .forms import CommentForm

from .models import Event, User, Ticket, RefundRequest
from .forms import RatingForm
from django.contrib import messages
from .models import Rating, Event
from .models import Event, User

from .models import Event, User, Venue


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


from .forms import RatingForm

@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    #Busca los ratings activos
    visible_ratings = event.rating_set.filter(bl_baja=False, is_current=True)
    
    user_rating = None
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(user=request.user, event=event, is_current=True, bl_baja=False).first()
    
    return render(request, "app/event_detail.html", {
        "event": event,
        "ratings": visible_ratings,
        "user_rating": user_rating
    })



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
def tickets(request):
    tickets = Ticket.objects.filter(user=request.user).order_by("buy_date")
    return render(request, "app/tickets.html",{"tickets":tickets})


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
        # Agregar un mensaje con el ticket_code
        messages.success(request, f"¡Compra exitosa! Código del ticket: {ticket.ticket_code}")
    
    return redirect('ticket_form', id=eventId)  # redirigimos al mismo formulario
        

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
from django.db import IntegrityError
from django.db.transaction import atomic

@login_required
def create_rating(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    
    if request.method == "POST":
        form = RatingForm(request.POST)
        rating_value = request.POST.get("rating", "0")
        
        if form.is_valid() and 1 <= int(rating_value) <= 5:
            # Desactiva los ratings del usuario
            Rating.objects.filter(
                event=event,
                user=request.user,
                is_current=True
            ).update(is_current=False)
            
            # Crear nueva calificación
            Rating.objects.create(
                event=event,
                user=request.user,
                title=form.cleaned_data['title'],
                text=form.cleaned_data['text'],
                rating=int(rating_value),
                is_current=True,
                bl_baja=False
            )
            messages.success(request, "Calificación guardada correctamente")
            return redirect("event_detail", id=event.id)
        else:
            messages.error(request, "Error en el formulario. Verifica los datos.")
    
    # Muestra formulario
    form = RatingForm()
    return render(request, "app/create_rating.html", {
        "form": form,
        "event": event
    })


@login_required
def update_rating(request, event_id, rating_id):
    event = get_object_or_404(Event, pk=event_id)
    rating = get_object_or_404(Rating, pk=rating_id, user=request.user)

    if request.method == "POST":
        form = RatingForm(request.POST, instance=rating)
        rating_value = request.POST.get("rating")

        try:
            rating_value = int(rating_value)
            if form.is_valid() and 1 <= rating_value <= 5:
                form.instance.rating = rating_value  # Asignamos el valor al modelo
                form.save()
                messages.success(request, "Calificación actualizada correctamente")
                return redirect("event_detail", id=event.id)
            else:
                messages.error(request, "La calificación debe estar entre 1 y 5 estrellas.")
        except (TypeError, ValueError):
            messages.error(request, "Por favor seleccioná una cantidad de estrellas.")

    else:
        form = RatingForm(instance=rating)

    return render(request, "rating/update_rating.html", {
        "form": form,
        "event": event,
        "rating": rating,
        "current_rating": rating.rating  # para inicializar las estrellas en el HTML
    })

@login_required
def list_ratings(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    ratings = event.rating_set.filter(bl_baja=False).order_by('-created_at')
    user_rating = ratings.filter(user=request.user).first()
    
    return render(request, "app/list_ratings.html", {
        "event": event,
        "ratings": ratings,
        "user_rating": user_rating
    })
@login_required
def delete_rating(request, event_id, rating_id):
    rating = get_object_or_404(Rating, id=rating_id, event_id=event_id)

    if request.user == rating.user or request.user == rating.event.organizer:
        rating.soft_delete()  #Manejo de la baja logica
        messages.success(request, "Calificación eliminada correctamente.")
    else:
        messages.error(request, "No tienes permiso para eliminar esta calificación.")

    return redirect('event_detail', id=event_id)
#####Venue

@login_required
def venue(request):
    venues = Venue.objects.filter(bl_baja=0)
    return render(request, "app/venue.html", {"venues":venues, "user_is_organizer": request.user.is_organizer },)

@login_required
def venue_form(request, id=None):    
    user = request.user

    if not user.is_organizer:
        messages.error(request, f'No posee los roles necesarios para acceder.')
        return redirect("venue")
    
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        direccion = request.POST.get("direccion")
        ciudad = request.POST.get("ciudad")
        capacidad = request.POST.get("capacidad")
        contacto= request.POST.get("contacto")
        if id is None:
            Venue.newVenue(nombre, direccion, ciudad,capacidad,contacto)
            messages.success(request, f'Se creo correctamente la ubicación "{nombre}".')
            return redirect("venue")
        else:
            venue = get_object_or_404(Venue, pk=id)
            venue.editarVenue(nombre, direccion, ciudad, capacidad,contacto)
            messages.success(request, f'Se modifico correctamente la ubicación "{venue.name}".')
            return redirect("venue")

    venue = {}
    if id is not None:
        try:
            venue = Venue.objects.get(pk=id)
            if venue.bl_baja:
                messages.error(request, f"No se puede acceder a la ubicación.")
                return redirect("venue")
            
        except Venue.DoesNotExist:
            messages.error(request, f"La ubicación solicitada no existe.")
            return redirect("venue")
        
        
    return render(request,"app/venue_form.html", {"venue":venue})

@login_required
def venue_baja(request,id=None):

    user = request.user
    if not user.is_organizer:
        messages.error(request, f'No se puede dar de baja la ubicacion ya que no posee los roles necesarios.')
        return redirect("venue")
    
    venue = {}
    
    if request.method == "POST":
        venue = get_object_or_404(Venue, pk=id)
        if venue.bl_baja:
            messages.error(request, f'No se puede  de baja la ubicacion ya que se encuentra dada de baja o no existe.')
        else:
            venue.venue_baja()
            messages.success(request, f'Se eliminó correctamente la ubicación "{venue.name}".')
            return redirect("venue")
    else:
        messages.error(request, f'No se puede dar de baja la ubicacion ya que se encuentra dada de baja o no existe.')
    return redirect("venue")

@login_required
def venue_detail(request, id=None):
    venue = {}
    try:
        venue = Venue.objects.get(pk=id)
        if venue.bl_baja:
            messages.error(request, f"No se puede acceder a la ubicación.")
            return redirect("venue")
        
    except Venue.DoesNotExist:
        messages.error(request, f"La ubicación solicitada no existe.")
        return redirect("venue")
    
    return render(request,"app/venue_detail.html", {"venue":venue,"user_is_organizer": request.user.is_organizer },)
