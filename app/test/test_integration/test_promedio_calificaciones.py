from django.test import TestCase, Client
from django.urls import reverse
from app.models import User, Venue, Category, Event, Rating
from django.utils import timezone

class AverageRatingIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Crear usuario organizador (dueño del evento)
        self.organizer = User.objects.create_user(
            username="organizador",
            password="password123",
            is_organizer=True
        )
        
        # Crear usuarios normales para las calificaciones
        self.user1 = User.objects.create_user(username="user1", password="pass")
        self.user2 = User.objects.create_user(username="user2", password="pass")
        self.user3 = User.objects.create_user(username="user3", password="pass")
        
        self.venue = Venue.objects.create(name="Test Venue", address="Somewhere")
        self.category = Category.objects.create(name="Test Category")

        # Crear evento perteneciente al organizador
        self.event = Event.objects.create(
            title="Evento prueba",
            description="Descripción de prueba",
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            organizer=self.organizer,  # ¡Importante! El organizador es el dueño
            venue=self.venue,
        )
        self.event.categories.add(self.category)

        # Crear calificaciones
        Rating.objects.create(
            event=self.event, user=self.user1, rating=5, 
            is_current=True, bl_baja=False, title="Excelente"
        )
        Rating.objects.create(
            event=self.event, user=self.user2, rating=3, 
            is_current=True, bl_baja=False, title="Regular"
        )
        # Calificación que no debería contar
        Rating.objects.create(
            event=self.event, user=self.user3, rating=1, 
            is_current=False, bl_baja=False
        )

    def test_organizer_can_see_average_rating(self):
            # 1. Autenticar como el organizador
            self.client.force_login(self.organizer)
        
            # 2. Acceder a la página de detalle del evento
            url = reverse('event_detail', kwargs={'id': self.event.id})
            response = self.client.get(url)
            
            # 3. Verificar que la respuesta es exitosa (200 OK)
            self.assertEqual(response.status_code, 200)
            
            # 4. Verificar que el promedio en el contexto es correcto
            self.assertEqual(response.context['avg_rating'], 4.0)  # (5 + 3) / 2
            
            # 5. Verificar que se muestra en el template (con coma decimal)
            content = response.content.decode()
            self.assertIn('Promedio: <strong>4,0</strong> de 5', content) #Me tiraba error porque la muestra era con strong
            
            # 6. Verificar que se muestran las calificaciones válidas
            self.assertContains(response, "Excelente")
            self.assertContains(response, "Regular")
            
            # 7. Verificar que NO se muestra la calificación inválida
            self.assertNotContains(response, "user3")  # is_current=False