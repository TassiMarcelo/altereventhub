from playwright.sync_api import expect
from app.test.test_e2e.base import BaseE2ETest

class SatisfactionSurveyE2ETest(BaseE2ETest):
    def test_submit_survey_successfully(self):
        user = self.create_test_user(username="usuario1", password="password123", email="u1@test.com")
        organizer = self.create_test_user(is_organizer=True)
        venue = self.create_test_venue(capacity=100)
        event = self.create_test_event(organizer, venue)
        ticket = self.create_test_ticket(user, event)
        
        self.login_user(username="usuario1", password="password123")

        self.page.goto(f"{self.live_server_url}/survey/{ticket.ticket_code}/")

        expect(self.page.locator("text=Encuesta")).to_be_visible()

        self.page.select_option("select[name='rating']","1")
        self.page.fill("textarea[name='comment']", "Anda muy lento")


        self.page.click("button:has-text('Enviar')") # va con una sola comilla con 2 se rompe

        self.page.wait_for_url(f"{self.live_server_url}/tickets")
        
        expect(self.page.locator("text=¡Gracias por contestar la encuesta!")).to_be_visible()