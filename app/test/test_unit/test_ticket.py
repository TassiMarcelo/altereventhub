import unittest
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from app.models import *
from app.views import *
from datetime import datetime
from django.core.exceptions import ValidationError
from django.test import TestCase
from app.models import User, Venue, Event, Ticket
from app.views import ticket_excede_capacidad_maxima
from django.utils import timezone


class TicketUsuarioLimiteTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="test_user")
        self.venue = Venue.objects.create(name="Teatro", capacity=100)
        self.event = Event.objects.create(
            title="Evento",
            description="Descripción del evento",
            scheduled_at=timezone.now(),
            organizer=self.user,
            venue=self.venue,
        )

    def test_usuario_hasta_4_tickets(self):
        # Total = 2 + 2 = 4
        Ticket.objects.create(user=self.user, event=self.event, quantity=2, buy_date=timezone.now())
        Ticket.objects.create(user=self.user, event=self.event, quantity=2, buy_date=timezone.now())

        resultado = Ticket.ticket_excede_limite_usuario(
            user_id=self.user.id, event_id=self.event.id, nueva_cantidad=0
        )
        self.assertFalse(resultado)

    def test_limite_4_tickets(self):
        t1 = Ticket.objects.create(
            user=self.user, event=self.event, quantity=3, buy_date=timezone.now()
        )
        Ticket.objects.create(user=self.user, event=self.event, quantity=1, buy_date=timezone.now())

        # Sumar 2, el total ahora sería 2 (nuevo) + 1 = 3, esta OK
        resultado = Ticket.ticket_excede_limite_usuario(
            user_id=self.user.id, event_id=self.event.id, nueva_cantidad=2, ticket_id=t1.id
        )
        self.assertFalse(resultado)

        # Sumar 4, excede
        resultado = Ticket.ticket_excede_limite_usuario(
            user_id=self.user.id, event_id=self.event.id, nueva_cantidad=4, ticket_id=t1.id
        )
        self.assertTrue(resultado)

    def test_editar_superando_limite(self):
        t1 = Ticket.objects.create(
            user=self.user, event=self.event, quantity=2, buy_date=timezone.now()
        )
        Ticket.objects.create(user=self.user, event=self.event, quantity=2, buy_date=timezone.now())

        # Modificar t1 a 3, el total sería 3 + 2 = 5, entonces excede
        resultado = Ticket.ticket_excede_limite_usuario(
            user_id=self.user.id, event_id=self.event.id, nueva_cantidad=3, ticket_id=t1.id
        )
        self.assertTrue(resultado)

    def test_editar_dentro_del_limite(self):
        t1 = Ticket.objects.create(
            user=self.user, event=self.event, quantity=2, buy_date=timezone.now()
        )
        Ticket.objects.create(user=self.user, event=self.event, quantity=1, buy_date=timezone.now())

        # Modificar t1 a 3, el total sería 3 + 1 = 4, por lo tanto es válido
        resultado = Ticket.ticket_excede_limite_usuario(
            user_id=self.user.id, event_id=self.event.id, nueva_cantidad=3, ticket_id=t1.id
        )
        self.assertFalse(resultado, "No debería exceder el límite de tickets")


# Verificar que al comprar un ticket con X lugares, no se sobrepase la capacidad de lugares del evento.
class TicketCapacidadTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="test_user")
        self.venue = Venue.objects.create(name="Teatro", capacity=100)
        self.event = Event.objects.create(
            title="Obra",
            description="Una obra de teatro",
            scheduled_at=datetime.now(),  # campo obligatorio
            organizer=self.user,
            venue=self.venue,
        )

    # Si el espacio tiene 90/100 lugares ocupados pero compro 10, el ticket NO excede la capacidad maxima
    def test_no_excede_capacidad(self):
        Ticket.objects.create(
            user=self.user, event=self.event, quantity=90, buy_date=datetime.now()
        )
        self.assertFalse(ticket_excede_capacidad_maxima(self.event, 10))

    # Si el espacio tiene 100/100 lugares ocupados y compro 10, el ticket SI excede la capacidad maxima
    def test_excede_capacidad(self):
        Ticket.objects.create(
            user=self.user, event=self.event, quantity=100, buy_date=datetime.now()
        )
        self.assertTrue(ticket_excede_capacidad_maxima(self.event, 1))
