from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from app.models import Event
from app.test.test_e2e.base import BaseE2ETest
from playwright.sync_api import expect
import re

class EventCountdownTest(BaseE2ETest):

    def setUp(self):
        super().setUp()
        self.organizer = self.create_test_user(username="organizador", is_organizer=True)
        self.user = self.create_test_user(username="usuario", is_organizer=False)
        self.venue = self.create_test_venue(capacity=100)

        scheduled_at = timezone.now() + timedelta(days=1)
        self.event = self.create_test_event(
            organizer=self.organizer,
            venue=self.venue,
            scheduled_at=scheduled_at,
            title="Evento de prueba"
        )

    def test_usuario_ve_countdown(self):
        self.login_user("usuario", "password123")
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/")

        countdown = self.page.locator("#countdown-text")
        expect(countdown).to_be_visible()
        pattern = re.compile(r"Faltan \d+ días?, \d+ horas? y \d+ minutos?")
        expect(countdown).to_have_text(pattern)

    def test_organizador_no_ve_countdown(self):
        self.login_user("organizador", "password123")
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/")
        countdown = self.page.locator("#countdown-text")
        expect(countdown).to_have_count(0)
