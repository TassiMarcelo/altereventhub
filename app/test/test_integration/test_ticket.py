from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from app.models import User, Event, Ticket, Venue
from django.db.models import Sum

class TicketIntegrationTest(TestCase):
    def setUp(self):
        self.user_password = 'contraseña'
        self.user = User.objects.create_user(
            username='prueba',
            password=self.user_password,
            email='prueba@ejemplo.com'
        )
        self.organizer = User.objects.create_user(
            username='organizador',
            password='contraseñaorganizador',
            email='organizador@evento.com',
            is_organizer=True
        )
        self.venue = Venue.objects.create(
            name='Estadio',
            address='Prueba 123',
            city='Ciudad prueba',
            capacity=1000,
            contact='contacto@prueba.com'
        )
        self.event = Event.objects.create(
            title='Evento prueba',
            description='descripcion',
            organizer=self.organizer,
            venue=self.venue,
            scheduled_at=timezone.now() + timezone.timedelta(days=1)
        )
        self.client.login(username=self.user.username, password=self.user_password)

    def test_limite_4_tickets(self):
        
        response = self.client.post(reverse('ticket_buy', args=[self.event.id]), {
            'quantity': 5,
            'type': 'GENERAL'
        })
        # Rechaza la compra
        self.assertNotEqual(response.status_code, 302)
        self.assertEqual(Ticket.objects.filter(user=self.user, event=self.event, bl_baja=0).count(), 0)
        print("Integración: compra de más de 4 tickets en un solo intento fue bloqueada correctamente")

    def test_compra_multiple_supera_limite(self):
        response = self.client.post(reverse('ticket_buy', args=[self.event.id]), {
            'quantity': 3,
            'type': 'GENERAL'
        })
        self.assertEqual(response.status_code, 302)

        # Intentar comprar 2 tickets más (supera el límite total de 4)
        response = self.client.post(reverse('ticket_buy', args=[self.event.id]), {
            'quantity': 2,
            'type': 'GENERAL'
        })
        self.assertNotEqual(response.status_code, 302)

        tickets = Ticket.objects.filter(user=self.user, event=self.event, bl_baja=0)
        self.assertEqual(tickets.aggregate(total=Sum('quantity'))['total'], 3)
        print("Integración: compra que excede el límite acumulado fue bloqueada correctamente")

    def test_editar_tickets(self):
        response = self.client.post(reverse('ticket_buy', args=[self.event.id]), {
            'quantity': 2,
            'type': 'GENERAL'
        })
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse('ticket_buy', args=[self.event.id]), {
            'quantity': 2,
            'type': 'GENERAL'
        })
        self.assertEqual(response.status_code, 302)

        tickets = Ticket.objects.filter(user=self.user, event=self.event, bl_baja=0)
        self.assertEqual(tickets.aggregate(total=Sum('quantity'))['total'], 4)

        # Editar uno de los tickets para superar el limite
        ticket = tickets.first()
        response = self.client.post(reverse('ticket_edit', args=[ticket.ticket_code]), {
            'quantity': 3,  # Cambio cantidad para que supere el limite
            'type': 'GENERAL'
        })
        self.assertEqual(response.status_code, 302)
        ticket.refresh_from_db()
        self.assertNotEqual(ticket.quantity, 3)
        print("Integración: edición que supera límite correctamente bloqueada")

        # Edito la cantidad dentro del limite permitido
        response = self.client.post(reverse('ticket_edit', args=[ticket.ticket_code]), {
            'quantity': 1,
            'type': 'GENERAL'
        })
        self.assertEqual(response.status_code, 302)
        ticket.refresh_from_db()
        self.assertEqual(ticket.quantity, 1)
        print("Integración: edición dentro del límite pasó correctamente")
