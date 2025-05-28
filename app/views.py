import datetime
from django.contrib.auth import authenticate, login
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages
from .models import Comment
from .forms import CommentForm
from django.http import JsonResponse
from django.db.models import Prefetch
from .models import Ticket, RefundRequest
from .forms import RatingForm
from django.contrib import messages
from .models import Rating
from django.core.exceptions import ValidationError
from .models import Event, User,Category
from django.db.models import Count
from .models import Venue, SatisfactionSurvey
from django.db import IntegrityError
from django.db.transaction import atomic
import logging
from .forms import RatingForm, SatisfactionSurveyForm
from django.db.models import Avg, Count

logger = logging.getLogger(__name__)

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
    tickets = Prefetch('tickets', queryset=Ticket.objects.filter(bl_baja=False))
    events = Event.objects.prefetch_related(tickets).order_by("scheduled_at")
    
    return render(
        request,
        "app/events.html",
        {"events": events, "user_is_organizer": request.user.is_organizer},
    )

@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)

    # Busca los ratings activos
    visible_ratings = event.rating_set.filter(bl_baja=False, is_current=True)

    # Promedio y cantidad de ratings
    rating_stats = visible_ratings.aggregate(
        promedio=Avg('rating'),
        cantidad=Count('id')
    )

    user_rating = None
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(user=request.user, event=event, is_current=True, bl_baja=False).first()

    return render(request, "app/event_detail.html", {
        "event": event,
        "ratings": visible_ratings,
        "user_rating": user_rating,
        "avg_rating": rating_stats["promedio"],
        "rating_count": rating_stats["cantidad"]
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
    
    categories = Category.objects.filter(is_active=True)
    selected_categories = []

    if request.method == "POST":  
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")
        venue_id = request.POST.get("venueSelect")
        status=request.POST.get("status")
        category_ids = request.POST.getlist("categories")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        selected_categories = Category.objects.filter(id__in=category_ids)
        venue = get_object_or_404(Venue, pk=venue_id)
        if id is None:
            Event.new(title, description,venue, scheduled_at, request.user, selected_categories)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description,venue,status, scheduled_at, request.user, selected_categories)

        return redirect("events")

    event = None
    if id is not None:
        event = get_object_or_404(Event, pk=id)
    venues = Venue.objects.filter(bl_baja=0)

    selected_categories = []
    if event:
        selected_categories = event.categories.values_list("id", flat=True)

    return render(
        request,
        "app/event_form.html",
        {"event": event, "venues":venues,"user_is_organizer": request.user.is_organizer, "categories": categories, "selected_categories": selected_categories},
    )




@login_required
def tickets(request):
    tickets = Ticket.objects.filter(user=request.user, bl_baja=0).order_by("buy_date")
    return render(request, "app/tickets.html",{"tickets":tickets})


@login_required
def ticket_delete(request,ticket_code):
    ticket = Ticket.objects.filter(ticket_code=ticket_code).first()
    if ticket:
        if request.user.is_organizer: #TODO: Verificar que sea el creador del evento del ticket
            ticket.soft_delete()
            print("ticket eliminado con exito!")
            return redirect("events")
        elif request.user.username == ticket.user.username:
            ticket.soft_delete()
            print("ticket eliminado con exito!")
            return redirect("tickets")
    return redirect("events")


@login_required
def ticket_edit(request, ticket_code):
    if request.method == "POST":
        quantity = request.POST.get("quantity")
        type = request.POST.get("type")
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messages.error(request, "La cantidad debe ser un número entero positivo.")
            return redirect("ticket_edit_form", ticket_code=ticket_code)

        if type not in Ticket.Type.values:
            messages.error(request, "El tipo de ticket no es válido.")
            return redirect("ticket_edit_form", ticket_code=ticket_code)

        ticket = Ticket.objects.filter(ticket_code=ticket_code, user=request.user).first()
        if not ticket:
            messages.error(request, "Ticket no encontrado.")
            return redirect("tickets")

        # Validar límite de 4 entradas por evento
        total_user_tickets = Ticket.objects.filter(
            user=request.user,
            event=ticket.event,
            bl_baja=0
        ).exclude(id=ticket.id).aggregate(Sum("quantity"))["quantity__sum"] or 0
        
        if total_user_tickets + quantity > 4:
            messages.error(request, f"No puedes tener más de 4 entradas por evento.")
            return redirect("ticket_edit_form", ticket_code=ticket_code)

        # Actualizar el ticket
        ticket.quantity = quantity
        ticket.type = type
        ticket.save()
        messages.success(request, "Ticket editado correctamente")
        return redirect("tickets")

    return redirect("tickets")


def ticket_edit_form(request,ticket_code):
    ticket = Ticket.objects.filter(ticket_code = ticket_code, user=request.user).first()
    return render(request, "app/ticket_edit_form.html",{"ticket":ticket})


def ticket_excede_capacidad_maxima(event, quantity):
    capacidad_maxima = event.venue.capacity
    capacidad_utilizada = Ticket.objects.filter(event=event, bl_baja=0).aggregate(total=Sum("quantity"))["total"] or 0
    print(f"capacidad utilizada: {capacidad_utilizada}")
    if(capacidad_utilizada+quantity>capacidad_maxima):
        return True
    else:
        return False
    

@login_required
def ticket_buy(request, eventId):
    user = request.user
    if request.method == "POST":
        quantity = request.POST.get("quantity")
        tipo = request.POST.get("type")

        # Validaciones básicas
        if not all([quantity, tipo]):
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect('ticket_form', id=eventId)
        
        quantity = int(quantity)
        try:
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messages.error(request, "La cantidad debe ser un número entero positivo.")
            return redirect('ticket_form', id=eventId)
        
        event = get_object_or_404(Event, pk=eventId)

        # Validar si hay cupos disponibles para el ticket
        if ticket_excede_capacidad_maxima(event,quantity):
            messages.error(request, "Lo sentimos, la capacidad maxima de entradas fue superada" )
            print("capacidad maxima SUPERADA")
            return redirect('ticket_form', id=eventId)

        if tipo not in Ticket.Type.values:
            messages.error(request, "El tipo de ticket no es válido.")
            return redirect('ticket_form', id=eventId)

        # Total de tickets comprados por el usuario
        total_user_tickets = Ticket.objects.filter(
            user=user, event=event, bl_baja=0
        ).aggregate(total=Sum("quantity"))["total"] or 0

        # Cantidad previa de tickets antes de la compra
        print(f"Usuario {user.username} ya tiene {total_user_tickets} tickets para evento {event.title}. Intentando comprar {quantity} más.")

        if total_user_tickets + quantity > 4:
            messages.error(request, f"No puedes comprar más de 4 entradas por evento.")
            print(f"Compra rechazada: el usuario quiere comprar {total_user_tickets + quantity}, que supera el límite.")
            return redirect('ticket_form', id=eventId)

        # Crear ticket
        print("Creando ticket...")
        ticket = Ticket.new(
            buy_date=timezone.now(),
            quantity=quantity,
            type=tipo,
            event=event,
            user=user
        )
        messages.success(request, f"¡Compra exitosa! Código del ticket: {ticket.ticket_code}")
        print(f"Ticket comprado! Codigo: {str(ticket.ticket_code)}")

        return redirect('satisfaction_survey', ticket_code=ticket.ticket_code)

    messages.error(request, "Método no permitido.")
    return redirect('ticket_form', id=eventId)
        

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
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en {field}: {error}")
    return redirect('event_detail', id=event.id)

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

@login_required
def my_refund(request):
    reembolsos_usuario = RefundRequest.objects.filter(requester=request.user)
    return render(request, "my_refund.html", {
        "reembolsos": reembolsos_usuario
    })

@login_required
def editar_reembolso(request, id):
    reembolso = get_object_or_404(RefundRequest, id=id, requester=request.user)

    if request.method == "POST":
        print("Datos recibidos:")
        print(f"Motivo: {request.POST.get('reason')}")
        print(f"Detalles: {request.POST.get('details')}")
        
        reembolso.reason = request.POST.get("reason")
        reembolso.details = request.POST.get("details")
        reembolso.save()
        messages.success(request, "Reembolso actualizado correctamente.")
        return redirect("my_refund")

    return render(request, "refund/edit_refund.html", {"reembolso": reembolso})

@login_required
def eliminar_reembolso(request, id):
    reembolso = get_object_or_404(RefundRequest, id=id, requester=request.user)

    if request.method == "POST":
        reembolso.delete()
        messages.success(request, "Reembolso eliminado correctamente.")
        return redirect("my_refund")

    return HttpResponseForbidden("Método no permitido.") 

 # Filtrar las solicitudes de reembolso x eventos del organizador
@login_required
def reembolsos_eventos(request):
    if not request.user.is_authenticated or not request.user.is_organizer:
        return render(request, '403.html')
    eventos_del_organizador = Event.objects.filter(organizer=request.user)
    tickets = Ticket.objects.filter(event__in=eventos_del_organizador)
    ticket_map = {str(ticket.ticket_code): ticket for ticket in tickets}
    refunds = RefundRequest.objects.filter(ticket_code__in=ticket_map.keys())

    for refund in refunds:
        refund.ticket = ticket_map.get(refund.ticket_code)
        refund.event = refund.ticket.event if refund.ticket else None
    
    return render(request, "reembolsos_eventos.html", {'refunds': refunds})    
def aprobar_reembolso(request, refund_id):
    refund = get_object_or_404(RefundRequest, id=refund_id)
    if request.method == 'POST':
        refund.approve()
        return JsonResponse({
            "status": "success",
            "new_status": refund.get_status_display()
        })
    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

def rechazar_reembolso(request, refund_id):
    refund = get_object_or_404(RefundRequest, id=refund_id)
    if request.method == 'POST':
        refund.reject()
        return JsonResponse({
            "status": "success",
            "new_status": refund.get_status_display()
        })
    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)



@login_required
def create_rating(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    user = request.user

    # Verificar si ya existe rating activo
    if Rating.objects.filter(user=user, event=event, is_current=True, bl_baja=False).exists():
        messages.error(request, "Ya has calificado este evento")
        return redirect('event_detail', id=event_id)

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        text = request.POST.get("text", "").strip()
        rating_value = request.POST.get("rating")

        rating_data = {
            "title": title,
            "text": text,
            "rating": rating_value,
            "event": event
        }

        errors = {}

        # Validación de título
        if not title:
            errors["title"] = "Por favor ingrese un título"

        # Validación de rating
        try:
            rating_int = int(rating_value)
            if rating_int < 1 or rating_int > 5:
                errors["rating"] = "La calificación debe estar entre 1 y 5"
        except (ValueError, TypeError):
            errors["rating"] = "La calificación debe ser un número válido"

        if errors:
            for field, error_msg in errors.items():
                messages.error(request, error_msg)
            return render(request, "rating/create_rating.html", {
                "errors": errors,
                "rating": rating_data,
                "event": event
            })

        # Crear el rating
        try:
            Rating.objects.create(
                user=user,
                event=event,
                title=title,
                text=text,
                rating=rating_int,
                is_current=True,
                bl_baja=False
            )
            messages.success(request, "¡Calificación guardada correctamente!")
            return redirect('event_detail', id=event.id)
            
        except Exception as e:
            messages.error(request, f"Error al guardar: {str(e)}")
            return render(request, "rating/create_rating.html", {
                "rating": rating_data,
                "event": event
            })

    return render(request, "rating/create_rating.html", {"event": event})


@login_required
def update_rating(request, event_id, rating_id):
    event = get_object_or_404(Event, pk=event_id)
    rating = get_object_or_404(Rating, pk=rating_id, user=request.user, event=event)

    if request.method == "POST":
        form = RatingForm(request.POST, instance=rating)
        if form.is_valid():
            try:
                # Guardar el formulario
                form.save()
                messages.success(request, "¡Calificación actualizada correctamente!")
                return redirect('event_detail', id=event.id)
                
            except Exception as e:
                messages.error(request, f"Error al guardar: {str(e)}")
        else:
            # Mostrar errores de validación
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # Inicializar formulario
        form = RatingForm(instance=rating)

    return render(request, "rating/update_rating.html", {
        'form': form,
        'event': event,
        'rating': rating
    })


@login_required
def list_ratings(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    ratings = event.rating_set.filter(bl_baja=False).order_by('-created_at')
    user_rating = ratings.filter(user=request.user).first()
    
    return render(request, "rating/list_ratings.html", {
        "event": event,
        "ratings": ratings,
        "user_rating": user_rating
    })


@login_required
def delete_rating(request, event_id, rating_id):
    rating = get_object_or_404(Rating, id=rating_id, event_id=event_id)

    if request.user != rating.user and request.user != rating.event.organizer:
        messages.error(request, "No tienes permiso para realizar esta acción")
        return redirect('event_detail', id=event_id)

    try:
        rating.soft_delete()
        messages.success(request, "Calificación eliminada correctamente")
    except Exception as e:
        logger.error(f"Error deleting rating: {str(e)}")
        messages.error(request, "Ocurrió un error al eliminar la calificación")

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
        
        #Guardo los datos enviados por el usuario para poder mostrarlos en caso de que no complete alguno de los campos
        #1)En caso de que haya venido del create, solo guardo los datos que estaban en el formulario.
        #2)En caso de que haya venido del update, guardo el id
        if id is None:
            venue_validate={
                "name": nombre,
                "address": direccion,
                "city": ciudad,
                "capacity": capacidad,
                "contact": contacto,
            }

        else:
            venue_validate={
                "id":id,
                "name": nombre,
                "address": direccion,
                "city": ciudad,
                "capacity": capacidad,
                "contact": contacto,
            }
             
        #Verifico cada campo para que no sea nulo
        errors = {}
        if nombre == "":
            errors["nombre"] = "Por favor ingrese un titulo"
        else:
            if len(nombre)>200:
                errors["nombre"] = "El valor ingresado es muy largo"

        if direccion == "":
            errors["direccion"] = "Por favor ingrese una descripcion"
        else:
            if len(direccion)>200:
                errors["direccion"] = "El valor ingresado es muy largo"
        
        if ciudad == "":
            errors["ciudad"] = "Por favor ingrese una ciudad"
        else:
            if len(ciudad)>200:
                errors["ciudad"] = "El valor ingresado es muy largo"
            
        if capacidad == "":
            errors["capacidad"] = "Por favor ingrese la capacidad"
        else:
            try:
                capacidad_num = int(capacidad)
                if capacidad_num <= 0:
                    errors["capacidad"] = "Por favor ingrese una cantidad mayor a 0"
            except ValueError:
                errors["capacidad"] = "Por favor ingrese un número válido"
            
        if contacto == "":
            errors["contacto"] = "Por favor ingrese un contacto"
        else:
            if len(contacto)>200:
                errors["contacto"] = "El valor ingresado es muy largo"

        #En caso de que haya errores, se reenvía el formulario con los mensajes correspondientes.
        if errors:
        # Renderizamos al form con errores y datos ingresados
            return render(request, "app/venue_form.html", {"errors": errors,"venue": venue_validate})

        
        #Si no se pasa ningun id significa que esta creando. caso contrario se modifica la ubicacion seleccionada.
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
        venue = get_object_or_404(Venue, pk=id,bl_baja=0)
        if venue.bl_baja:
            messages.error(request, f'No se puede  de baja la ubicacion ya que se encuentra dada de baja o no existe.')
        else:
            eventos_activos = venue.events.all()
            
            if eventos_activos:
                messages.error(request, f'No se puede  de baja la ubicacion ya que se encuentra en Eventos.')
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
        

@login_required
def category_list(request):
    categories = Category.objects.annotate(event_count=Count("events_categories__id"))
    return render(request, "app/category_list.html", {"categories": categories})
                  
@login_required
def category_form(request, id=None):
    if not request.user.is_organizer:
        return redirect("category_list")
    
    category =None
    if id:
        category = get_object_or_404(Category, pk=id)

    errors ={}

    if request.method =="POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description","")
        is_active = request.POST.get("is_active") == "on"

        errors = Category.validateCategory(name, description, category_id=category.id if category else None)
        
        if not errors:
            if category:
                category.name = name
                category.description = description
                category.is_active = is_active
            else:
                category = Category(name=name, description=description, is_active=is_active)  
            try:
                category.clean()
                category.save()
                return redirect("category_list")
            except ValidationError as e:
                errors= e.message_dict

        return render(
            request,
            "app/category_form.html",
            {"category": category, "errors": errors},
         )

    return render( request, "app/category_form.html", {"category": category, "errors":errors})

@login_required
def category_delete(request, id):
    if not request.user.is_organizer:
        return redirect("category_list")
    
    category = get_object_or_404(Category, pk=id)

    if category.events.exists():
        messages.error(request, "No se puede eliminar la categoría porque tiene eventos asociados.")
        return redirect("category_list")
    
    if category.is_active:
        messages.error(request, "No se puede eliminar una categoría activa.")
        return redirect("category_list")

    category.delete()
    messages.success(request, "Categoría eliminada exitosamente.")
    return redirect("category_list")

def category_events(request, id):
    category = get_object_or_404(Category, id=id)
    events = category.events_categories.all()
    return render(request, "app/category_events.html", {"category": category, "events": events})

#Encuesta de compra
@login_required
def satisfaction_survey(request, ticket_code):
    ticket = get_object_or_404(Ticket, ticket_code=ticket_code, user=request.user)

    if hasattr(ticket, "satisfactionsurvey"):
        messages.info(request, "Ya completaste la encuesta para este ticket")
        return redirect("tickets")

    if request.method == "POST":
        form = SatisfactionSurveyForm(request.POST)
        if form.is_valid():
            survey = form.save(commit=False)
            survey.user = request.user
            survey.ticket =ticket
            survey.save()
            messages.success(request, "¡Gracias por contestar la encuesta!")
            return redirect("tickets")
    else:
        form = SatisfactionSurveyForm()
    return render(request, "survey/satisfaction_form.html", {"form": form, "ticket":ticket})
        
