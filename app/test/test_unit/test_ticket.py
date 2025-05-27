from unittest.mock import patch, MagicMock
import unittest

from django.core.exceptions import ValidationError
from app.models import Ticket

class TicketUsuarioLimiteTest(unittest.TestCase):

    @patch('app.models.Ticket.objects.filter')  # mockeamos el queryset filter
    def test_usuario_hasta_4_tickets(self, mock_filter):
        ticket1 = MagicMock(quantity=2, id=1)
        ticket2 = MagicMock(quantity=2, id=2)
        mock_filter.return_value = [ticket1, ticket2]

        resultado = Ticket.ticket_excede_limite_usuario(user_id=1, event_id=1, nueva_cantidad=0)
        self.assertFalse(resultado)

    @patch('app.models.Ticket.objects.filter')
    def test_limite_4_tickets(self, mock_filter):
        ticket1 = MagicMock(id=1, quantity=3)
        ticket2 = MagicMock(id=2, quantity=1)
        mock_filter.return_value = [ticket1, ticket2]

        # Sumar nueva cantidad 2 al ticket 1
        resultado = Ticket.ticket_excede_limite_usuario(user_id=1, event_id=1, nueva_cantidad=2, ticket_id=1)
        self.assertFalse(resultado, "No debe exceder el límite con 2 + 1 = 3")
        
        # Sumar nueva cantidad 4 al ticket 1, excede
        resultado = Ticket.ticket_excede_limite_usuario(user_id=1, event_id=1, nueva_cantidad=4, ticket_id=1)
        self.assertTrue(resultado)

    @patch('app.models.Ticket.objects.filter')
    def test_editar_superando_limite(self, mock_filter):
        ticket1 = MagicMock(quantity=2, id=1)
        ticket2 = MagicMock(quantity=2, id=2)
        mock_filter.return_value = [ticket1, ticket2]

        resultado = Ticket.ticket_excede_limite_usuario(user_id=1, event_id=1, nueva_cantidad=3, ticket_id=1)
        self.assertTrue(resultado)

    @patch('app.models.Ticket.objects.filter')
    def test_editar_dentro_del_limite(self, mock_filter):
        ticket1 = MagicMock(id=1, quantity=2)
        ticket2 = MagicMock(id=2, quantity=1)
        mock_filter.return_value = [ticket1, ticket2]

        t1 = MagicMock(id=1, user=MagicMock(id=1), event=MagicMock(id=1), quantity=3)

        def mock_clean():
            if Ticket.ticket_excede_limite_usuario(
                user_id=t1.user.id,
                event_id=t1.event.id,
                nueva_cantidad=t1.quantity,
                ticket_id=t1.id
            ):
                raise ValidationError("No puedes tener más de 4 tickets para un mismo evento.")

        t1.clean = mock_clean

        try:
            t1.clean()
        except ValidationError:
            self.fail("ValidationError fue lanzado incorrectamente al editar dentro del límite")

if __name__ == '__main__':
    unittest.main()
