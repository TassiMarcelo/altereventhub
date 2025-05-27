import re
import datetime
from django.utils import timezone
from playwright.sync_api import expect
from app.test.test_e2e.base import BaseE2ETest
from app.models import Event, User, Venue


class EventCountdownTest(BaseE2ETest):
    def setUp(self):
        super().setUp()
      
        self.organizer = User.objects.create_user(
            username="organizador",
            email="org@example.com",
            password="password123",
            is_organizer=True,
        )
        self.regular_user = User.objects.create_user(
            username="usuario",
            email="user@example.com",
            password="password123",
            is_organizer=False,
        )
        self.venue = Venue.objects.create(name="Test Venue", address="123 Calle")

        future_date = timezone.now() + datetime.timedelta(days=1, hours=2, minutes=30)
        self.future_event = Event.objects.create(
            title="Evento con Countdown",
            description="Evento futuro con contador",
            scheduled_at=future_date,
            organizer=self.organizer,
            venue=self.venue
        )

    def test_countdown_visible_for_regular_user(self):
        """Verifica que un usuario regular ve el countdown en el detalle del evento"""
        self.login_user("usuario", "password123")

        self.page.goto(f"{self.live_server_url}/events/{self.future_event.id}/")

        self.page.wait_for_selector("#countdown-text", state="visible")
        countdown = self.page.locator("#countdown-text")
        expect(countdown).to_be_visible()

        text = countdown.inner_text()
        print(f"[DEBUG] Countdown visible con texto: '{text}'")


    def test_countdown_not_visible_for_organizer(self):
        """Verifica que el organizador NO ve el countdown en el detalle del evento"""
        self.login_user("organizador", "password123")

        self.page.goto(f"{self.live_server_url}/events/{self.future_event.id}/")

        countdown = self.page.locator("#countdown-text")
        expect(countdown).to_have_count(0)  