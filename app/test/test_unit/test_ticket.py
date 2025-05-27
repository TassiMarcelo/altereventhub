from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from app.models import Ticket, Event, User, Venue

class TicketLogicTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='prueba', password='12345')
        self.venue = Venue.objects.create(
            name='Estadio prueba',
            address='Calle Falsa 123'
        )
        self.event = Event.objects.create(
            title='Evento prueba',
            description='Descripcion',
            scheduled_at=timezone.now(),
            organizer=self.user,
            venue=self.venue
        )

    def test_usuario_hasta_4_tickets(self):
        Ticket.objects.create(user=self.user, event=self.event, quantity=2, buy_date=timezone.now(), type=Ticket.Type.GENERAL)
        Ticket.objects.create(user=self.user, event=self.event, quantity=2, buy_date=timezone.now(), type=Ticket.Type.GENERAL)
        tickets = Ticket.objects.filter(user=self.user, event=self.event, bl_baja=False)
        total_quantity = sum(ticket.quantity for ticket in tickets)
        self.assertLessEqual(total_quantity, 4)
        print("✅ test_usuario_hasta_4_tickets pasó correctamente")

    def test_limite_4_tickets(self):
        Ticket.objects.create(user=self.user, event=self.event, quantity=3, buy_date=timezone.now(), type=Ticket.Type.GENERAL)
        Ticket.objects.create(user=self.user, event=self.event, quantity=1, buy_date=timezone.now(), type=Ticket.Type.GENERAL)

        try:
            Ticket.objects.create(user=self.user, event=self.event, quantity=1, buy_date=timezone.now(), type=Ticket.Type.GENERAL)
        except ValidationError:
            print("✅ test_limite_4_tickets detectó correctamente exceso de tickets")
        else:
            self.fail("ValidationError no fue lanzado al exceder el límite de tickets")

    def test_editar_dentro_del_limite(self):
        t1 = Ticket.objects.create(user=self.user, event=self.event, quantity=2, buy_date=timezone.now(), type=Ticket.Type.GENERAL)
        t1.quantity = 3
        t1.save()
        tickets = Ticket.objects.filter(user=self.user, event=self.event, bl_baja=False)
        total_quantity = sum(ticket.quantity for ticket in tickets)
        self.assertLessEqual(total_quantity, 4)
        print("✅ test_editar_dentro_del_limite pasó correctamente")

    def test_editar_superando_limite(self):
        t1 = Ticket.objects.create(user=self.user, event=self.event, quantity=2, buy_date=timezone.now(), type=Ticket.Type.GENERAL)
        t2 = Ticket.objects.create(user=self.user, event=self.event, quantity=2, buy_date=timezone.now(), type=Ticket.Type.GENERAL)

        t1.quantity = 3
        try:
            t1.save()
        except ValidationError:
            print("✅ test_editar_superando_limite detectó correctamente exceso al editar ticket")
        else:
            self.fail("ValidationError no fue lanzado al editar ticket y exceder límite")
