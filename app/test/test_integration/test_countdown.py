import time
from freezegun import freeze_time
import datetime
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from app.models import Event, Venue
from django.contrib.auth import get_user_model

User = get_user_model()

class CountdownIntegrationTest(TestCase):

    def setUp(self):
        self.organizer = User.objects.create_user(username='org', password='pass123', is_organizer=True)
        self.attendee = User.objects.create_user(username='user1', password='pass123', is_organizer=False)
        self.venue = Venue.objects.create(name="Test Venue", address="123 Calle")
        self.event = Event.objects.create(
            title='Concierto',
            description='Concierto',
            scheduled_at=timezone.now() + timezone.timedelta(minutes=2),  
            organizer=self.organizer,
            venue=self.venue,
        )

    def test_countdown_actualiza_minutos(self):
        self.client.login(username='user1', password='pass123')
        url = reverse('countdown_json', args=[self.event.id])
        initial_time = timezone.now()
        
        with freeze_time(initial_time):
            response1 = self.client.get(url)
            self.assertEqual(response1.status_code, 200)
            data1 = response1.json()
            self.assertEqual(data1['days'], 0)
            self.assertEqual(data1['hours'], 0)
            self.assertTrue(data1['minutes'] > 0)
       
        future_time = initial_time + datetime.timedelta(seconds=61)

        with freeze_time(future_time):
            response2 = self.client.get(url)
            self.assertEqual(response2.status_code, 200)
            data2 = response2.json()
            self.assertEqual(data2['days'], 0)
            self.assertEqual(data2['hours'], 0)
            self.assertTrue(data2['minutes'] < data1['minutes'])
