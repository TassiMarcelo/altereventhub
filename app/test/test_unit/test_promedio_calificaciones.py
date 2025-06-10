from django.test import SimpleTestCase
from app.utils import calculate_average_rating

class CalculateAverageRatingTest(SimpleTestCase):

    class FakeRating:
        def __init__(self, rating, is_current=True, bl_baja=False):
            self.rating = rating
            self.is_current = is_current
            self.bl_baja = bl_baja

    def test_calculate_average_rating_filters_and_averages_correctly(self):
        ratings = [
            self.FakeRating(5),
            self.FakeRating(3),
            self.FakeRating(4, is_current=False),   # excluido
            self.FakeRating(1, bl_baja=True)        # excluido
        ]
        result = calculate_average_rating(ratings)
        self.assertEqual(result, 4.0)  # (5 + 3) / 2