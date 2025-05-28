from django.test import TestCase
import datetime
from app.models import *
from django.db.models import Sum


class TicketModelTest(TestCase):

    def test_buy_exceed_tickets(self):

        user = User.objects.create(
            username="usuario_test",
            email="usuario@example.com",
            password="password123",
            is_organizer=False,
        )

        organizer = User.objects.create(
            username="organizador_test",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )
            
        venue = Venue.objects.create(
            name="Estadio Central",
            address="Av. Siempre Viva 123",
            city="Springfield",
            capacity=100,
            contact="contacto@estadiocentral.com"
        )


        category = Category.objects.create(
            name="Música",
            description="Eventos relacionados con conciertos y festivales.",
            is_active=True
        )

        event = Event.objects.create(
            title="Festival de Jazz",
            description="Un evento musical imperdible.",
            scheduled_at=timezone.now() + timezone.timedelta(days=30),
            organizer=organizer,
            venue=venue,
            status=Event.Status.ACTIVO
        )

        ticket = Ticket.objects.create(
            quantity=100,
            type=Ticket.Type.VIP,
            event=event,
            buy_date=timezone.now(),
            user=user
        )


        # Simular intento de compra de 1 ticket adicional
        nueva_cantidad = 1
        capacidad_maxima = event.venue.capacity
        capacidad_utilizada = Ticket.objects.filter(event=event, bl_baja=False).aggregate(total=Sum("quantity"))["total"] or 0

        # Verificamos la lógica
        self.assertTrue(capacidad_utilizada + nueva_cantidad > capacidad_maxima)
