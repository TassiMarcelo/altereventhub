from unittest import TestCase
from unittest.mock import patch, MagicMock
from app.models import *
from app.views import *

class TicketModelTest(TestCase):

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
