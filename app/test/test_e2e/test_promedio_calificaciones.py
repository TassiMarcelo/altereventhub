from django.contrib.auth import get_user_model
from django.utils import timezone
from playwright.sync_api import expect
from app.models import Venue, Category, Event, Rating
from app.test.test_e2e.base import BaseE2ETest

class EventRatingE2ETest(BaseE2ETest):
    """Pruebas E2E para la visualización de calificaciones por parte del organizador"""
    
    def setUp(self):
        super().setUp()
        # Configurar datos de prueba
        self.organizer = get_user_model().objects.create_user(
            username="organizador",
            email="organizador@example.com",
            password="password123",
            is_organizer=True
        )
        
        self.venue = Venue.objects.create(name="Venue Test", address="123 Calle")
        self.category = Category.objects.create(name="Categoría Test")
        
        self.event = Event.objects.create(
            title="Evento con Calificaciones",
            description="Evento para probar calificaciones",
            scheduled_at=timezone.now() + timezone.timedelta(days=7),
            organizer=self.organizer,
            venue=self.venue,
        )
        self.event.categories.add(self.category)
        
        # Crear algunas calificaciones
        users = [
            get_user_model().objects.create_user(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password="password123"
            ) for i in range(1, 5)
        ]
        
        Rating.objects.create(
            event=self.event, 
            user=users[0], 
            rating=5, 
            is_current=True,
            title="Excelente evento",
            text="Me encantó todo"
        )
        Rating.objects.create(
            event=self.event, 
            user=users[1], 
            rating=3, 
            is_current=True,
            title="Evento regular",
            text="Podría mejorar"
        )
        Rating.objects.create(
            event=self.event, 
            user=users[2], 
            rating=4, 
            is_current=False
        )
        Rating.objects.create(
            event=self.event, 
            user=users[3], 
            rating=1, 
            is_current=True, 
            bl_baja=True
        )
    
    def test_organizer_can_see_average_rating(self):
        """Verifica que el organizador pueda ver el promedio de calificaciones de su evento"""
        # Iniciar sesión como organizador
        self.login_user("organizador", "password123")
        
        # Navegar a la página del evento
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/")
        
        # 1. Verificar que estamos en la página correcta
        expect(self.page).to_have_url(f"{self.live_server_url}/events/{self.event.id}/")
        expect(self.page.get_by_text(self.event.title)).to_be_visible()
        
        # 2. Verificar que se muestra la sección de calificaciones
        expect(self.page.get_by_text("Calificaciones (2)")).to_be_visible()  # Solo 2 calificaciones válidas
        
        # 3. Verificar que el organizador ve el promedio (en la sección de detalles)
        expect(self.page.get_by_text("Promedio: 4,0 de 5")).to_be_visible()
        
        # 4. Verificar las estrellas del promedio
        stars = self.page.locator(".stars span")
        expect(stars).to_have_count(5)
        expect(stars.nth(0)).to_have_css("color", "rgb(255, 215, 0)")  # ★ dorada
        expect(stars.nth(1)).to_have_css("color", "rgb(255, 215, 0)")  # ★ dorada
        expect(stars.nth(2)).to_have_css("color", "rgb(255, 215, 0)")  # ★ dorada
        expect(stars.nth(3)).to_have_css("color", "rgb(255, 215, 0)")  # ★ dorada
        expect(stars.nth(4)).to_have_css("color", "rgb(211, 211, 211)")  # ★ gris
        
        # 5. Verificar que se muestran las calificaciones individuales válidas
        expect(self.page.get_by_text("Excelente evento")).to_be_visible()
        expect(self.page.get_by_text("Evento regular")).to_be_visible()
        expect(self.page.get_by_text("user1")).to_be_visible()
        expect(self.page.get_by_text("user2")).to_be_visible()
        
        # 6. Verificar que NO se muestran las calificaciones inválidas
        expect(self.page.get_by_text("user3")).not_to_be_visible()
        expect(self.page.get_by_text("user4")).not_to_be_visible()