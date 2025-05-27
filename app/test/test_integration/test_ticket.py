from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from app.models import *
import datetime
from django.db.models import Sum

class TicketIntegrationSimplifiedTest(TestCase):
    def setUp(self):
        self.password = "contraseña123"
        self.user = User.objects.create_user(username="usuario_test", password=self.password, email="user@test.com")
        self.organizer = User.objects.create_user(username="organizador_test", password="passorg", email="org@test.com", is_organizer=True)
        self.venue = Venue.objects.create(name="Estadio Central", address="Av. Siempre Viva 123", city="La plata", capacity=100, contact="contact@venue.com")
        self.event = Event.objects.create(title="Evento Test", description="Evento para test", organizer=self.organizer, venue=self.venue, scheduled_at=timezone.now() + timezone.timedelta(days=10))
        self.client.login(username=self.user.username, password=self.password)

    def test_comprar_dentro_del_limite(self):
        # Compra válida
        response = self.client.post(reverse('ticket_buy', args=[self.event.id]), {
            'quantity': 4,
            'type': 'GENERAL'
        })
        self.assertEqual(response.status_code, 302)
        total = Ticket.objects.filter(user=self.user, event=self.event, bl_baja=0).aggregate(total=Sum('quantity'))['total'] or 0
        self.assertEqual(total, 4)

    def test_comprar_excediendo_limite(self):
        # Excede el limite
        response = self.client.post(reverse('ticket_buy', args=[self.event.id]), {
            'quantity': 5,
            'type': 'GENERAL'
        }, follow=True)
        self.assertContains(response, "No puedes comprar más de 4 entradas por evento.")
        total = Ticket.objects.filter(user=self.user, event=self.event, bl_baja=0).aggregate(total=Sum('quantity'))['total'] or 0
        self.assertEqual(total, 0)

    def test_comprar_varias_veces_superando_limite_acumulado(self):
        # Compra inicial 3 tickets
        response1 = self.client.post(reverse('ticket_buy', args=[self.event.id]), {
            'quantity': 3,
            'type': 'GENERAL'
        })
        self.assertEqual(response1.status_code, 302)

        # Excede el limite
        response2 = self.client.post(reverse('ticket_buy', args=[self.event.id]), {
            'quantity': 2,
            'type': 'GENERAL'
        }, follow=True)
        self.assertContains(response2, "No puedes comprar más de 4 entradas por evento.")

        total = Ticket.objects.filter(user=self.user, event=self.event, bl_baja=0).aggregate(total=Sum('quantity'))['total'] or 0
        self.assertEqual(total, 3)

    def test_editar_tickets_a_cantidad_valida(self):
        # Compra inicial 2 tickets
        self.client.post(reverse('ticket_buy', args=[self.event.id]), {
            'quantity': 2,
            'type': 'GENERAL'
        })

        ticket = Ticket.objects.filter(user=self.user, event=self.event, bl_baja=0).first()

        # Editar ticket para aumentar cantidad a 3
        response = self.client.post(reverse('ticket_edit', args=[ticket.ticket_code]), {
            'quantity': 3,
            'type': 'GENERAL'
        })
        self.assertEqual(response.status_code, 302)

        ticket.refresh_from_db()
        self.assertEqual(ticket.quantity, 3)

    def test_editar_tickets_excediendo_limite(self):
        # Compra inicial 3 tickets
        self.client.post(reverse('ticket_buy', args=[self.event.id]), {
            'quantity': 3,
            'type': 'GENERAL'
        })

        # Compra otro ticket
        self.client.post(reverse('ticket_buy', args=[self.event.id]), {
            'quantity': 1,
            'type': 'GENERAL'
        })

        tickets = Ticket.objects.filter(user=self.user, event=self.event, bl_baja=0)
        ticket = tickets.first()

        # Intentar editar el primer ticket a 4,excede
        response = self.client.post(reverse('ticket_edit', args=[ticket.ticket_code]), {
            'quantity': 4,
            'type': 'GENERAL'
        }, follow=True)
        self.assertContains(response, "No puedes tener más de 4 entradas por evento.")

        ticket.refresh_from_db()
        self.assertNotEqual(ticket.quantity, 4)



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
