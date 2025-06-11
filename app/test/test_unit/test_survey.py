from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from app.models import User, Venue, Category, Event, Ticket, SatisfactionSurvey

class SatisfactionSurveyModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="usuario1", password="contraseña1"
        )
        venue = Venue.objects.create(name="lugar", address="calle ", city="ciudad", capacity=100, contact="hola@gmail.com")
        category = Category.objects.create(name="cumbia", description="altocumbion", is_active=True)
        event = Event.objects.create(
            title="Evento",
            description="El evento",
            scheduled_at=timezone.now() + timedelta(days=1),
            venue=venue,
            organizer=self.user
        )
        event.categories.add(category)
        self.ticket =Ticket.objects.create(
            user=self.user,
            event=event,
            quantity=1,
            buy_date=timezone.now(),
            type=Ticket.Type.GENERAL
            )

    def test_crear_encuesta(self):
        encuesta = SatisfactionSurvey.objects.create(
            user=self.user,
            ticket=self.ticket,
            rating=4,
            comment="muy malo se rompe todo jaja"
        )

        self.assertIsNotNone(encuesta.pk)
        self.assertEqual(encuesta.rating, 4)
        self.assertEqual(encuesta.comment, "muy malo se rompe todo jaja")

    def test_rating_no_valido(self):
        encuesta= SatisfactionSurvey(
            user = self.user,
            ticket=self.ticket,
            rating=10,
            comment="messi"
        )

        with self.assertRaises(ValidationError):
            encuesta.full_clean() #estamos validando y tiene que tirar el error

    def test_crear_dos_encuestas_para_mismo_ticket(self):
        SatisfactionSurvey.objects.create(
            user=self.user,
            ticket=self.ticket,
            rating=5,
            comment="Primera encuesta"
        )
        with self.assertRaises(IntegrityError):
            SatisfactionSurvey.objects.create(
                user=self.user,
                ticket=self.ticket,
                rating=3,
                comment="intento 9mil"
            )

    def test_encuesta_sin_comentario(self):
        encuesta = SatisfactionSurvey(
            user=self.user,
            ticket=self.ticket,
            rating=3
        )
        encuesta.full_clean()

    def test_no_permitir_hacer_encuesta_sin_rating(self):
        encuesta = SatisfactionSurvey(
                user=self.user,
                ticket=self.ticket,
                comment="No existe el rating"
            )
        with self.assertRaises(ValidationError):
            encuesta.full_clean()

    def test_rating_negativo(self):
        encuesta= SatisfactionSurvey(
            user=self.user,
            ticket=self.ticket,
            rating=-1,
            comment="Esto no deberias ser valido pq es negativo"
        )

        with self.assertRaises(ValidationError):
            encuesta.full_clean()            