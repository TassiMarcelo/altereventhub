from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from app.models import Event, User, Venue, Category

class EventCountdownTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', username='tester', password='pass123')
        self.venue = Venue.objects.create(name="Test Venue", address="123 Calle")
        self.category = Category.objects.create(name="Test Category")

    def test_countdown_future_event(self):
        scheduled_time = timezone.now() + timedelta(days=1, hours=2, minutes=30)
        event = Event.objects.create(
            title="Evento futuro",
            description="Descripción",
            scheduled_at=scheduled_time,
            organizer=self.user,
            venue=self.venue,
        )
        event.categories.add(self.category)

        countdown = event.countdown

        self.assertEqual(countdown['days'], 1)
        self.assertEqual(countdown['hours'], 2)
        self.assertTrue(29 <= countdown['minutes'] <= 31)

    def test_countdown_past_event(self):
        scheduled_time = timezone.now() - timedelta(hours=1)
        event = Event.objects.create(
            title="Evento pasado",
            description="Descripción",
            scheduled_at=scheduled_time,
            organizer=self.user,
            venue=self.venue,
        )
        event.categories.add(self.category)

        countdown = event.countdown
        self.assertEqual(countdown['days'], 0)
        self.assertEqual(countdown['hours'], 0)
        self.assertEqual(countdown['minutes'], 0)
