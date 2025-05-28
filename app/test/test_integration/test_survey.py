from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from app.models import User, Event, Ticket, Venue, Category, SatisfactionSurvey

class SatisfactionSurveyViewTest(TestCase):
    def setUp(self):
        self.user =User.objects.create_user(
            username="usuario_test",
            email="usuario1@test.com",
            password="contraseña1"
        )
        self.client.login(username="usuario_test", password="contraseña1")

        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@gmail.com",
            password="contraseñaor",
            is_organizer=True
        )

        self.venue = Venue.objects.create(
            name="Estadio Test",
            address="Calle Falsa xD",
            city="Springfield",
            capacity=100,
            contact="contacto@test.com"
        )

        self.category =Category.objects.create(
            name="Conciertos",
            description="Listos para el rock ?",
            is_active=True
        )

        self.event =Event.objects.create(
            title="Concierto de musica xd",
            description="El evento ",
            scheduled_at=timezone.now()+timezone.timedelta(days=10),
            organizer=self.organizer,
            venue=self.venue,
            status=Event.Status.ACTIVO
        )

        self.ticket = Ticket.objects.create(
            user=self.user,
            event=self.event,
            quantity=1,
            type=Ticket.Type.GENERAL,
            buy_date=timezone.now()
        )

    def test_acceso_formulario_encuesta(self):
        """El usuario puede acceder al formulario de la encuesta"""
        url = reverse("satisfaction_survey", args=[self.ticket.ticket_code])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,"Encuesta")

    
    def test_envio_encuesta_valida(self):
        """El usuario puede evniar una encuesta"""
        url = reverse("satisfaction_survey", args=[self.ticket.ticket_code])
        data= {
            "rating":1,
            "comment":"Malo se rompio",
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("tickets"))
        self.assertTrue(SatisfactionSurvey.objects.filter(ticket=self.ticket).exists())

    def test_no_permitir_segunda_encuesta(self):
        """No permiter enviar una encuesta por el mismo ticket"""
        SatisfactionSurvey.objects.create(
            user=self.user,
            ticket=self.ticket,
            rating=5,
            comment="Malo"
        )
        url =reverse("satisfaction_survey", args=[self.ticket.ticket_code])
        response = self.client.get(url)
        self.assertRedirects(response, reverse("tickets"))
