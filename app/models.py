from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

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
    

    def clean(self):
        if not self.name.strip():
            raise ValidationError("El nombre de la categoria no puede estar vacio")

        existing = Category.objects.filter(name=self.name, is_active=True)
        if self.pk:
            existing = existing.exclude(pk=self.pk) 

        if self.is_active and existing.exists():
            raise ValidationError("El nombre de la categoria ya existe")

    def __str__(self):
        return self.name    


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    categories = models.ManyToManyField(Category, related_name="events", blank=True)

    def __str__(self):
        return self.title

    @classmethod
    def validate(cls, title, description, scheduled_at, categories=None):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

        if categories is None or len(categories) == 0:
            errors["categories"] = "Por favor ingrese al menos una categoria"

        return errors

    @classmethod
    def new(cls, title, description, scheduled_at, organizer, categories=None):
        errors = cls.validate(title, description, scheduled_at, categories)

        if errors:
            return False, errors

        event = cls.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
        )
        if categories:
            event.categories.set(categories)
        return True, None

    def update(self, title, description, scheduled_at, organizer, categories=None):
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer

        self.save()

        if categories is not None:
            self.categories.set(categories)
        return True
