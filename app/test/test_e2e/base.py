import os

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import sync_playwright

from app.models import User
from app.models import *

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
headless = os.environ.get("HEADLESS", 1) == 1
slow_mo = os.environ.get("SLOW_MO", 0)


class BaseE2ETest(StaticLiveServerTestCase):
    """Clase base con la configuración común para todos los tests E2E"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=headless, slow_mo=int(slow_mo))

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def setUp(self):
        # Crear un contexto y página de Playwright
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

    def tearDown(self):
        # Cerrar la página después de cada test
        self.page.close()

    def create_test_user(self,username="usuario_test",password="password123",email="test@example.com", is_organizer=False):
        """Crea un usuario de prueba en la base de datos"""
        User.objects.filter(username=username).delete()
        user =  User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_organizer=is_organizer,
        )
        user.save()
        return user
    

    def create_test_category(self,name="Musica"):
        return Category.objects.create(
            name=name,
            description="Eventos relacionados con conciertos y festivales.",
            is_active=True
        )
    
    def create_test_venue(self,capacity:int,name="Estadio Central"):
        return Venue.objects.create(
            name=name,
            address="Av. Siempre Viva 123",
            city="Springfield",
            capacity=capacity,
            contact="contacto@estadiocentral.com"
        )
    
    def create_test_event(self,organizer,venue,scheduled_at=timezone.now() + timezone.timedelta(days=30),title="Festival de Jazz"):
        return Event.objects.create(
        title=title,
        description="Un evento musical imperdible.",
        scheduled_at=scheduled_at,
        organizer=organizer,
        venue=venue,
        status=Event.Status.ACTIVO
    )

    
    def login_user(self, username, password):
        """Método auxiliar para iniciar sesión"""
        self.page.goto(f"{self.live_server_url}/accounts/login/")
        self.page.get_by_label("Usuario").fill(username)
        self.page.get_by_label("Contraseña").fill(password)
        self.page.click("button[type='submit']")
