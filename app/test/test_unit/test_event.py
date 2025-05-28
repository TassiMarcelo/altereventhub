from datetime import timedelta, datetime
from django.test import TestCase
from django.utils import timezone
from app.models import Event, User,Venue,Category

class EventModelTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador_test",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )

    def test_event_creation(self):
        self.venue = Venue.objects.create(name="Test Venue",address="Test Address",city="Test City",capacity=100,contact="test@venue.com")
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + timedelta(days=1),
            venue=self.venue,
            organizer=self.organizer,
        )
        """Test que verifica la creación correcta de eventos"""
        self.assertEqual(event.title, "Evento de prueba")
        self.assertEqual(event.description, "Descripción del evento de prueba")
        self.assertEqual(event.organizer, self.organizer)
        self.assertEqual(event.venue, self.venue)
        self.assertIsNotNone(event.created_at)
        self.assertIsNotNone(event.updated_at)

    def test_event_validate_with_valid_data(self):
        """Test que verifica la validación de eventos con datos válidos"""
        scheduled_at = timezone.now() + timedelta(days=1)
        self.categoria=Category.objects.create(name="Categoria nombre",description="Descripcion categoria",is_active=True)
        self.venue = Venue.objects.create(name="Test Venue",address="Test Address",city="Test City",capacity=100,contact="test@venue.com")
        errors = Event.validate("Título válido", "Descripción válida",self.venue,scheduled_at,[self.categoria])
        self.assertEqual(errors, {})

    def test_event_validate_with_empty_title(self):
        """Test que verifica la validación de eventos con título vacío"""
        self.categoria=Category.objects.create(name="Categoria nombre",description="Descripcion categoria",is_active=True)
        self.venue = Venue.objects.create(name="Test Venue",address="Test Address",city="Test City",capacity=100,contact="test@venue.com")
        scheduled_at = timezone.now() + timedelta(days=1)
        errors = Event.validate("", "Descripción válida",self.venue,scheduled_at,[self.categoria])
        self.assertIn("title", errors)
        self.assertEqual(errors["title"], "Por favor ingrese un titulo")

    def test_event_validate_with_empty_description(self):
        """Test que verifica la validación de eventos con descripción vacía"""
        self.categoria=Category.objects.create(name="Categoria nombre",description="Descripcion categoria",is_active=True)
        self.venue = Venue.objects.create(name="Test Venue",address="Test Address",city="Test City",capacity=100,contact="test@venue.com")
        scheduled_at = timezone.now() + timedelta(days=1)
        errors = Event.validate("Título válido", "",self.venue,scheduled_at,[self.categoria])
        self.assertIn("description", errors)
        self.assertEqual(errors["description"], "Por favor ingrese una descripcion")

    def test_event_new_with_valid_data(self):
        """Test que verifica la creación de eventos con datos válidos"""
        self.venue = Venue.objects.create(name="Test Venue",address="Test Address",city="Test City",capacity=100,contact="test@venue.com")
        scheduled_at = timezone.now() + timedelta(days=2)
        self.category = Category.objects.create(name="Categoria de prueba", description="Descripcion", is_active=True)
        success, errors = Event.new(
            title="Nuevo evento",
            description="Descripción del nuevo evento",
            venue=self.venue,
            scheduled_at=scheduled_at,
            organizer=self.organizer,
            categories=[self.category],
        )

        self.assertTrue(success)
        self.assertIsNone(errors)

        # Verificar que el evento fue creado en la base de datos
        new_event = Event.objects.get(title="Nuevo evento")
        self.assertEqual(new_event.description, "Descripción del nuevo evento")
        self.assertEqual(new_event.organizer, self.organizer)

    def test_event_new_with_invalid_data(self):
        """Test que verifica que no se crean eventos con datos inválidos"""
        self.venue = Venue.objects.create(name="Test Venue",address="Test Address",city="Test City",capacity=100,contact="test@venue.com")
        self.category = Category.objects.create(name="Categoria de prueba", description="Descripcion", is_active=True)

        scheduled_at = timezone.now() + timedelta(days=2)
        initial_count = Event.objects.count()

        # Intentar crear evento con título vacío
        success, errors = Event.new(
            title="",
            description="Descripción del evento",
            venue=self.venue,
            scheduled_at=scheduled_at,
            organizer=self.organizer,
            categories=[self.category],
        )

        self.assertFalse(success)
        self.assertIn("title", errors)

        # Verificar que no se creó ningún evento nuevo
        self.assertEqual(Event.objects.count(), initial_count)
    
    def test_event_update(self):
        """Test que verifica la actualización de eventos"""
        new_title = "Título actualizado"
        new_description = "Descripción actualizada"
        new_scheduled_at = timezone.now() + timedelta(days=3)
        self.venue = Venue.objects.create(name="Test Venue",address="Test Address",city="Test City",capacity=100,contact="test@venue.com")
        self.category = Category.objects.create(name="Categoria de prueba", description="Descripcion", is_active=True)
       
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + timedelta(days=1),
            venue=self.venue,
            organizer=self.organizer,
        )

        event.update(
            title=new_title,
            description=new_description,
            venue=event.venue,
            status=event.status,
            scheduled_at=new_scheduled_at,
            organizer=self.organizer,
            categories=[self.category],
        )

        # Recargar el evento desde la base de datos
        updated_event = Event.objects.get(pk=event.pk)

        self.assertEqual(updated_event.title, new_title)
        self.assertEqual(updated_event.description, new_description)
        self.assertEqual(updated_event.scheduled_at.time(), new_scheduled_at.time())

    def test_event_update_partial(self):
        """Test que verifica la actualización parcial de eventos"""
        self.venue = Venue.objects.create(name="Test Venue",address="Test Address",city="Test City",capacity=100,contact="test@venue.com")
        self.category = Category.objects.create(name="Categoria de prueba", description="Descripcion", is_active=True)

        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + timedelta(days=1),
            venue=self.venue,
            organizer=self.organizer,
        )

        original_title = event.title
        original_scheduled_at = event.scheduled_at
        new_description = "Solo la descripción ha cambiado"

        event.update(
            title=None,  # No cambiar
            description=new_description,
            venue=event.venue,
            status=event.status,
            scheduled_at=None,  # No cambiar
            organizer=None,  # No cambiar
            categories=[self.category],
        )

        # Recargar el evento desde la base de datos
        updated_event = Event.objects.get(pk=event.pk)

        # Verificar que solo cambió la descripción
        self.assertEqual(updated_event.title, original_title)
        self.assertEqual(updated_event.description, new_description)
        self.assertEqual(updated_event.scheduled_at, original_scheduled_at)

      
class EventStatusModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.venue = Venue.objects.create(name="Test Venue",address="Test Address",city="Test City",capacity=100,contact="test@venue.com")
        self.event = Event.objects.create(
            title="Evento de prueba",
            description="Prueba de estado por defecto",
            scheduled_at=datetime.now() + timedelta(days=1),
            organizer=self.user,
            venue=self.venue
        )

    def test_estado_por_defecto_es_activo(self):
        self.assertEqual(self.event.status, Event.Status.ACTIVO)

    def test_puede_cambiarse_a_cancelado(self):
        self.event.status = Event.Status.CANCELADO
        self.event.save()
        self.assertEqual(self.event.status, Event.Status.CANCELADO)