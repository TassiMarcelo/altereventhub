from django.test import SimpleTestCase
from django.utils import timezone
from datetime import timedelta
from app.models import Event

class EventCountdownTest(SimpleTestCase):
    def test_countdown_future_event(self):
        scheduled_time = timezone.now() + timedelta(days=1, hours=2, minutes=30)
        event = Event(
            scheduled_at=scheduled_time
        )

        countdown = event.countdown

        self.assertEqual(countdown['days'], 1)
        self.assertEqual(countdown['hours'], 2)
        self.assertTrue(29 <= countdown['minutes'] <= 31)

    def test_countdown_past_event(self):
        scheduled_time = timezone.now() - timedelta(hours=1)
        event = Event(
            scheduled_at=scheduled_time
        )

        countdown = event.countdown
        self.assertEqual(countdown['days'], 0)
        self.assertEqual(countdown['hours'], 0)
        self.assertEqual(countdown['minutes'], 0)
