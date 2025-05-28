from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
import uuid
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
import re

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

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    events = models.ManyToManyField("Event", related_name="category_events", blank=True)
    
    @classmethod
    def validateCategory(cls, name, description=None, category_id=None):
        error = {}

        if not name or not name.strip():  # verifica que se escriba algo y no este en blanco o tenga un espacio
            error["name"]= "El nombre de la categoria no puede estar vacio"  

        existing = cls.objects.filter(name=name.strip()) #Para poder editar sin que tome que el nombre de la categoria ya existe
        if category_id:
            existing = existing.exclude(pk=category_id)
        if existing.exists():
            
            error["name"]= "El nombre de la categoria ya existe"

        if not description or not description.strip():
            error["description"]= "Ingrese la descripcion de la categoria"
        elif not re.match(r'^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]+$', description.strip()):
            error["description"]= "La descripcion solo puede contener letras y numeros"

        return error

    @classmethod
    def newCategory(cls,name, description=None, is_active=True):
        errors =cls.validateCategory(name, description)
        if len(errors) > 0:
            return False, errors
        
        category = cls.objects.create(
            name=name.strip(),
            description=description.strip() if description else "", #nos ayuda a no crear una categoria sin descripcion
            is_active=is_active
        )
        return True, None
        
    def __str__(self):
        return self.name    


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
    def newVenue(cls, name,address,city,capacity,contact):

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
    class Status(models.TextChoices):
        ACTIVO = 'Activo', 'Activo'
        CANCELADO = 'Cancelado', 'Cancelado'
        REPROGRAMADO = 'Reprogramado', 'Reprogramado'
        AGOTADO = 'Agotado', 'Agotado'
        FINALIZADO = 'Finalizado', 'Finalizado'


    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="events")
    status = models.CharField(
    max_length=20,
    choices=Status.choices,
    default=Status.ACTIVO
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    categories = models.ManyToManyField(Category, related_name="events_categories", blank=True)

    def __str__(self):
        return self.title

    def average_rating(self):
        return self.ratings.filter(bl_baja=False, is_current=True).aggregate(avg_rating=Avg('rating'))['avg_rating']
    
    @classmethod
    def validate(cls, title, description,venue,scheduled_at, categories=None):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

        if venue is None:
            errors["venueSelect"] = "Por favor ingrese una ubicacion"
        
        if categories is None or len(categories) == 0:
            errors["categories"] = "Por favor ingrese al menos una categoria"

        return errors


    @property
    def active_tickets(self):
        return self.tickets.filter(bl_baja=False)

    @property
    def countdown(self):
        now = timezone.now()
        if self.scheduled_at <= now:
            return {'days': 0, 'hours': 0, 'minutes': 0}

        delta: timedelta = self.scheduled_at - now
        total_seconds = int(delta.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        return {
            'days': days,
            'hours': hours,
            'minutes': minutes
        }

    @classmethod
    def new(cls, title, description,venue, scheduled_at, organizer, categories=None):
        errors = cls.validate(title, description,venue, scheduled_at, categories)

        if errors:
            return False, errors

        event = cls.objects.create(
            title=title,
            description=description,
            venue=venue,
            scheduled_at=scheduled_at,
            organizer=organizer,
        )
        if categories:
            event.categories.set(categories)
        return True, None

    def update(self, title, description,venue,status, scheduled_at, organizer, categories=None):
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer
        self.venue = venue or self.venue
        self.status= status or self.status
        self.save()
        if categories is not None:
            self.categories.set(categories)
        return True
        
# Realizar la alta, baja y modificación. El formulario de creación y edición debe tener validaciones server-side.
'''
[ok] ticket_code es un valor autogenerado en el backend

[ok] Un usuario REGULAR puede comprar, y eliminar sus tickets. 

[ok] Hacer formulario para datos de tarjeta

[ok] Un usuario organizador puede eliminar tickets de sus eventos. (si el usuario es de tipo organizador, puede eliminar tickets)

[ok] Un usuario REGULAR editar sus tickets.  

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

    def clean(self):
        errors = {}
        if not self.ticket_code.strip():
            errors["ticket_code"] = "Ingrese el código del ticket"
        if not self.reason.strip():
            errors["reason"] = "Seleccione un motivo válido"

        if errors:
            raise ValidationError(errors)

    @classmethod
    def new(cls, ticket_code, reason, details, requester):
        refund = cls(
            ticket_code=ticket_code,
            reason=reason,
            details=details,
            requester=requester,
        )
        try:
            refund.full_clean()
            refund.save()
            return True, None
        except ValidationError as e:
            return False, e.message_dict

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
    
    def save(self, *args, **kwargs):
        self.full_clean()  
        super().save(*args, **kwargs)



class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    text = models.TextField(blank=True)
    rating = models.IntegerField()
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

    @classmethod
    def newRating(cls, user, event, title, rating, text=None):
        try:
            cls.objects.create(
                user=user,
                event=event,
                title=title,
                rating=rating,
                text=text or ''
            )
            return True, None
        except Exception as e:
            return False, {'db_error': str(e)}

    def soft_delete(self):
        """Eliminación lógica sin validaciones"""
        self.bl_baja = True
        self.is_current = False
        self.save()

class SatisfactionSurvey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.ticket.ticket_code} - {self.rating}"