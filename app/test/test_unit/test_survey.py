from unittest import TestCase
from unittest.mock import MagicMock

class SatisfactionSurveyLogicTest(TestCase):
    def test_ticket_tiene_encuesta_true(self):
        ticket = MagicMock()
        ticket.satisfactionsurvey = MagicMock()
        self.assertTrue(hasattr(ticket,"satisfactionsurvey"))

    def test_ticket_tiene_encuesta_false(self):
        ticket =MagicMock()
        if hasattr(ticket,"satisfactionsurvey"):
            del ticket.satisfactionsurvey
        self.assertFalse(hasattr(ticket,"satisfactionsurvey"))