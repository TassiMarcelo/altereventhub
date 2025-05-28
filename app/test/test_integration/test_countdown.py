from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from app.models import Event, Venue
from django.contrib.auth import get_user_model

User = get_user_model()

class CountdownIntegrationTest(TestCase):

    def setUp(self):
        self.organizer = User.objects.create_user(username='org', password='pass123', is_organizer=True)
        self.venue = Venue.objects.create(name="Test Venue", address="123 Calle")
        self.event = Event.objects.create(
            title='Concierto',
            description='Concierto',
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
        )
        self.attendee = User.objects.create_user(username='user1', password='pass123', is_organizer=False)

    def test_countdown_visible_for_non_organizer_after_login(self):
        login = self.client.login(username='user1', password='pass123')
        self.assertTrue(login)  
        url = reverse('event_detail', args=[self.event.id])
        response = self.client.get(url)
        self.assertContains(response, 'id="countdown-text"')
        self.assertContains(response, 'Cargando countdown...')

    def test_countdown_not_visible_for_organizer(self):
        self.client.login(username='org', password='pass123')
        url = reverse('event_detail', args=[self.event.id])
        response = self.client.get(url)
        self.assertNotContains(response, 'id="countdown-text"')
        self.assertNotContains(response, 'Cargando countdown...')