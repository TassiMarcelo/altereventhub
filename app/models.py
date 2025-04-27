from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

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


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @classmethod
    def validate(cls, title, description, scheduled_at):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

        return errors

    @classmethod
    def new(cls, title, description, scheduled_at, organizer):
        errors = Event.validate(title, description, scheduled_at)

        if len(errors.keys()) > 0:
            return False, errors

        Event.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
        )

        return True, None

    def update(self, title, description, scheduled_at, organizer):
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer

        self.save()


# Realizar la alta, baja y modificación. El formulario de creación y edición debe tener validaciones server-side.
'''
[ok] ticket_code es un valor autogenerado en el backend

[pendiente] Un usuario REGULAR puede comprar, editar y eliminar sus tickets. 

[pendiente] Hacer formulario para datos de tarjeta

[pendiente] Un usuario organizador puede eliminar tickets de sus eventos. (si el usuario es de tipo organizador, puede eliminar tickets)

[pendiente] Más adelante se agregaron controles de tiempo. Por ejemplo, podrá editar y eliminar dentro de los 30
minutos de que la entrada fue comprada (ESTO NO ES OBLIGATORIO)
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

        # TODO: Validaciones

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
        self.buy_date = buy_date or self.buy_date
        self.quantity = quantity or self.quantity
        self.type = type or self.type
        self.event = event or self.event
        self.user = user or self.user

        self.save()

    def soft_delete(self): # Baja lógica
        self.bl_baja = True
        self.save()
