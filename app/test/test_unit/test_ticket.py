from unittest.mock import patch, MagicMock
import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock
from app.models import *
from app.views import *
from django.core.exceptions import ValidationError
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



    @patch('app.models.Ticket.objects.filter')
    def test_no_excede_capacidad(self, mock_filter):
        # Crear un mock para el objeto Event con venue.capacity
        mock_venue = MagicMock(capacity=100)
        mock_event = MagicMock(venue=mock_venue)

        # Mockear el aggregate para devolver 90 tickets vendidos
        # Ahora por mas que nadie haya comprado tickets, habra 90 espacios ocupados
        mock_queryset = MagicMock()
        mock_queryset.aggregate.return_value = {'total': 90}
        mock_filter.return_value = mock_queryset

        # Compro 10 tickets mas, llenando por completo el espacio
        resultado = ticket_excede_capacidad_maxima(mock_event, 10)
        self.assertFalse(resultado) # Deberia devolver false, ya que no sobrepasamos el limite

    @patch('app.models.Ticket.objects.filter')
    def test_excede_capacidad(self, mock_filter):
        mock_venue = MagicMock(capacity=100)
        mock_event = MagicMock(venue=mock_venue)

        mock_queryset = MagicMock()
        mock_queryset.aggregate.return_value = {'total': 100}
        mock_filter.return_value = mock_queryset

        # El espacio ya esta lleno, voy a intentar comprar un ticket solo
        resultado = ticket_excede_capacidad_maxima(mock_event, 1)
        self.assertTrue(resultado) # Deberia devolver true, ya que sobrepasamos el limite
        if __name__ == '__main__':
            unittest.main()
