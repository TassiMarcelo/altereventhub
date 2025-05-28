from app.models import User, Venue, Category, Event, Rating
from django.test import TestCase
from django.utils import timezone

class AverageRatingIntegrationTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="pass")
        self.user2 = User.objects.create_user(username="user2", password="pass")
        self.user3 = User.objects.create_user(username="user3", password="pass")
        self.user4 = User.objects.create_user(username="user4", password="pass")

        self.venue = Venue.objects.create(name="Test Venue", address="Somewhere")
        self.category = Category.objects.create(name="Test Category")

        self.event = Event.objects.create(
            title="Evento prueba",
            description="Descripción de prueba",
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            organizer=self.user1,
            venue=self.venue,
        )
        self.event.categories.add(self.category)

        # Ratings con usuarios distintos (solo se contarán los válidos)
        Rating.objects.create(event=self.event, user=self.user1, rating=5, is_current=True, bl_baja=False)
        Rating.objects.create(event=self.event, user=self.user2, rating=3, is_current=True, bl_baja=False)
        Rating.objects.create(event=self.event, user=self.user3, rating=4, is_current=False, bl_baja=False) 
        Rating.objects.create(event=self.event, user=self.user4, rating=1, is_current=True, bl_baja=True)   

    def test_average_rating_method(self):
        avg = self.event.average_rating()
        self.assertEqual(avg, 4.0)  # (5 + 3) / 2