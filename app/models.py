from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

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

# intervengo

class RefundRequest(models.Model):
    approved = models.BooleanField(default=False)
    #convertir el ticket_code de ticket a string para compararlo con este str(ticket.ticket_code) == refund_request.ticket_code
    ticket_code = models.CharField(max_length=255)
    reason = models.TextField()
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
    def new(cls, ticket_code, reason, requester):
        errors = cls.validate(ticket_code, reason)

        if errors:
            return False, errors

        cls.objects.create(
            ticket_code=ticket_code,
            reason=reason,
            requester=requester,
        )

        return True, None

    def approve(self):
        self.approved = True
        self.approval_date = timezone.now()
        self.save()

    def update(self, ticket_code=None, reason=None, approved=None, approval_date=None):
        if ticket_code:
            self.ticket_code = ticket_code
        if reason:
            self.reason = reason
        self.save()
