from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    is_organizer = models.BooleanField(default=False)

    @classmethod
    def validate_new_user(cls, email, username, password, password_confirm):
        errors = {}

        if email is None:
            errors["email"] = "El email es requerido"
        elif User.objects.filter(email=email).exists():
            errors["email"] = "Ya existe un usuario con este email"

        if username is None:
            errors["username"] = "El username es requerido"
        elif User.objects.filter(username=username).exists():
            errors["username"] = "Ya existe un usuario con este nombre de usuario"

        if password is None or password_confirm is None:
            errors["password"] = "Las contraseñas son requeridas"
        elif password != password_confirm:
            errors["password"] = "Las contraseñas no coinciden"

        return errors


class Venue(models.Model):
    name=models.CharField(max_length=200)
    address= models.CharField(max_length=200)
    city= models.CharField(max_length=200)
    capacity = models.IntegerField(default=0)
    contact=models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    bl_baja= models.BooleanField(default=False)

    @classmethod
    def validateVenues(cls, name,address,city,capacity,contact):
        errors = {}

        if name == "":
            errors["nombre"] = "Por favor ingrese un titulo"

        if address == "":
            errors["direccion"] = "Por favor ingrese una descripcion"
        
        if city == "":
            errors["ciudad"] = "Por favor ingrese una ciudad"
            
        if capacity == "":
            errors["capacidad"] = "Por favor ingrese la capacidad"
            
        if contact == "":
            errors["contacto"] = "Por favor ingrese un contacto"
        return errors
    
    @classmethod
    def newVenue(cls, name,address,city,capacity,contact):
        errors = Venue.validateVenues(name,address,city,capacity,contact)
        if len(errors.keys()) > 0:
            return False, errors
        Venue.objects.create(
            name=name,
            address=address,
            city=city,
            capacity=capacity,
            contact=contact,
        )
        return True, None
    
    def venue_baja(self):
        self.bl_baja= True
        self.save()

    def editarVenue(self,name,address,city,capacity,contact):
        self.name= name or self.name
        self.address=address or self.address
        self.city=city or self.city
        self.capacity= capacity or self.capacity
        self.contact=contact or self.contact
        self.save()



class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    def __str__(self):
        return self.title

    @classmethod
    def validate(cls, title, description,venue, scheduled_at):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

        if venue is None:
            errors["venueSelect"] = "Por favor ingrese una ubicacion"
        
        return errors


    @property
    def active_tickets(self):
        return self.tickets.filter(bl_baja=False)

    @classmethod
    def new(cls, title, description,venue, scheduled_at, organizer):
        errors = Event.validate(title, description,venue,scheduled_at)

        if len(errors.keys()) > 0:
            return False, errors
        
        Event.objects.create(
            title=title,
            description=description,
            venue=venue,
            scheduled_at=scheduled_at,
            organizer=organizer,
        )

        return True, None

    def update(self, title, description,venue, scheduled_at, organizer):
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer
        self.venue = venue or self.venue
        self.save()


# Realizar la alta, baja y modificación. El formulario de creación y edición debe tener validaciones server-side.
'''
[ok] ticket_code es un valor autogenerado en el backend

[ok] Un usuario REGULAR puede comprar, y eliminar sus tickets. 

[ok] Hacer formulario para datos de tarjeta

[ok] Un usuario organizador puede eliminar tickets de sus eventos. (si el usuario es de tipo organizador, puede eliminar tickets)

[pendiente] Un usuario REGULAR editar sus tickets. 

[pendiente] Más adelante se agregaron controles de tiempo. Por ejemplo, podrá editar y eliminar dentro de los 30 minutos de que la entrada fue comprada (ESTO NO ES OBLIGATORIO)
'''
class Ticket(models.Model):
    quantity = models.IntegerField()
    class Type(models.TextChoices):
        GENERAL = 'GENERAL', 'General'
        VIP = 'VIP', 'VIP'
    type = models.CharField( 
        max_length=7,          
        choices=Type.choices,
        default=Type.GENERAL,
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets") # Desde evento, podemos acceder a los tickets gracias a related_name
    buy_date = models.DateTimeField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets") # El usuario comprador del evento
    ticket_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    bl_baja = models.BooleanField(default=False) # Campo para el borrado lógico

    def __str__(self) -> str:
        return str(self.ticket_code)
    
    @classmethod
    def new(cls, buy_date, quantity, type, event, user): # Alta

        # Asociar al comprador (User) y al evento (Event)
        ticket = cls.objects.create(
            buy_date=buy_date,
            quantity=quantity,
            type=type,
            event=event,
            user=user
            )
        return ticket

    def update(self, buy_date=None, quantity=None, type=None, event=None, user=None): # Modificación
        self.quantity = quantity or self.quantity
        self.type = type or self.type
        self.save()

    def soft_delete(self): # Baja lógica
        self.bl_baja = True
        self.save()


#models para comment
class Comment(models.Model):
    title = models.CharField(max_length=100, verbose_name="Título")
    text = models.TextField(verbose_name="Texto del comentario")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Fecha de creación")
    
    # Relación con User (un usuario muchos comentarios)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Usuario"
    )
    
    # Relación con Event (un evento muchos comentarios)
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Evento"
    )

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    class Meta:
        ordering = ['-created_at']  # Ordenar por fecha descendente
        verbose_name = "Comentario"
        verbose_name_plural = "Comentarios"
# intervengo

REASON_CHOICES = [
    ('no_asistencia', 'Impedimento para asistir'),
    ('evento_cancelado', 'Evento modificado'),
    ('error_compra', 'Error en la compra'),
]

class RefundRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pendiente', 'Pendiente'
        APPROVED = 'aprobado', 'Aprobado'
        REJECTED = 'rechazado', 'Rechazado'

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    ticket_code = models.CharField(max_length=255)
    reason = models.CharField(max_length=100, choices=REASON_CHOICES)
    details = models.TextField(blank=True, default="")
    approval_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refund_requests")

    def __str__(self):
        return f"Refund {self.ticket_code}"

    @classmethod
    def validate(cls, ticket_code, reason):
        errors = {}

        if ticket_code == "":
            errors["ticket_code"] = "Por favor ingrese el código del ticket"
        if reason == "":
            errors["reason"] = "Por favor ingrese el motivo del reembolso"

        return errors

    @classmethod
    def new(cls, ticket_code, reason, details, requester):
        errors = cls.validate(ticket_code, reason)
        if errors:
            return False, errors

        cls.objects.create(
            ticket_code=ticket_code,
            reason=reason,
            details=details,
            requester=requester,
        )
        return True, None

    def approve(self):
        self.status = self.Status.APPROVED
        self.approval_date = timezone.now()
        self.save()

    def reject(self):
        self.status = self.Status.REJECTED
        self.approval_date = timezone.now()
        self.save()

    def update(self, ticket_code=None, reason=None):
        if ticket_code:
            self.ticket_code = ticket_code
        if reason:
            self.reason = reason
        self.save()


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    text = models.TextField(blank=True)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    bl_baja = models.BooleanField(default=False)
    is_current = models.BooleanField(default=True)

    class Meta:
        constraints = [
        models.UniqueConstraint(
            fields=['user', 'event'],
            condition=models.Q(is_current=True, bl_baja=False),
            name='unique_active_rating_per_user_event'
        )
    ]
    #Eliminacion logica
    def soft_delete(self):
        """Marcar como eliminado lógicamente"""
        self.bl_baja = True
        self.is_current = False
        self.save()
