import re
import time
from playwright.sync_api import expect
from app.test.test_e2e.base import BaseE2ETest
from app.models import *

class TicketModelTest(BaseE2ETest):
    """Tests relacionados con la compra de tickets"""
    
    def setUp(self):
        super().setUp()
        # Limpiar cookies antes de cada test
        self.page.context.clear_cookies()
        
    def tearDown(self):
        # Limpieza adicional si es necesaria
        super().tearDown()

    def test_cannot_buy_more_than_4_tickets(self):
        # Crear datos con identificadores únicos
        timestamp = str(int(time.time()))
        
        organizer = self.create_test_user(
            is_organizer=True,
            username=f"organizador_{timestamp}"
        )
        venue = self.create_test_venue(capacity=100)
        event = self.create_test_event(organizer, venue)

        buyer = self.create_test_user(
            is_organizer=False,
            username=f"comprador_{timestamp}",
            password="contraseña",
            email=f"hello_{timestamp}@gmail.com"
        )
        
        self.login_user(username=buyer.username, password="contraseña")
        self.page.goto(f"{self.live_server_url}/ticket/{event.id}/form/")
        
        # Esperar a que el formulario cargue completamente
        self.page.wait_for_selector("select[name='type']")
        
        # Completar formulario
        self.page.select_option("select[name='type']", "GENERAL")
        self.page.fill("input[name='quantity']", "5")
        self.page.fill("input[name='card_number']", "1234 5678 9012 3456")
        self.page.fill("input[name='card_expiry']", "12/26")
        self.page.fill("input[name='card_cvv']", "123")
        self.page.check("#terms")

        # Manejar alerta
        alert_message = {}
        def handle_dialog(dialog):
            alert_message['text'] = dialog.message
            dialog.dismiss()
        
        self.page.on("dialog", handle_dialog)
        self.page.click("button:has-text('Comprar')")
        self.page.wait_for_timeout(1000)

        assert 'text' in alert_message, "No se disparó ningún alert"
        assert "máximo" in alert_message['text'].lower() or "4" in alert_message['text']

    def test_ticket_buy_exceeds_capacity(self):
        # Crear datos con identificadores únicos
        timestamp = str(int(time.time()))
        
        organizer = self.create_test_user(
            is_organizer=True,
            username=f"org_{timestamp}"
        )
        venue = self.create_test_venue(1)  # Capacidad muy limitada
        event = self.create_test_event(organizer, venue)

        user = self.create_test_user(
            is_organizer=False,
            username=f"usr_{timestamp}",
            password="contra129*",
            email=f"email_{timestamp}@gmail.com"
        )
        
        self.login_user(username=user.username, password="contra129*")
        self.page.goto(f"{self.live_server_url}/ticket/{event.id}/form/")
        
        # Esperar a que el formulario cargue
        self.page.wait_for_selector("select[name='type']")
        
        # Completar formulario
        self.page.goto(f"{self.live_server_url}/ticket/{event.id}/form/") # Ir a la compra de entradas para el evento

        # Rellenar el formulario
        self.page.select_option("select[name='type']", "GENERAL")
        self.page.fill("input[name='quantity']", "2")
        self.page.fill("input[name='card_number']", "1234 5678 9012 3456")
        self.page.fill("input[name='card_expiry']", "12/12")
        self.page.fill("input[name='card_cvv']", "123")
        self.page.check("#terms")

        # Manejar alerta
        alert_message = {}
        def handle_dialog(dialog):
            alert_message['text'] = dialog.message
            dialog.dismiss()
        
        self.page.on("dialog", handle_dialog)
        self.page.click("button:has-text('Comprar')")
        self.page.wait_for_timeout(1000)

        assert 'text' in alert_message, "No se disparó ningún alert"
        assert "capacidad" in alert_message['text'].lower()


    def test_ticket_reembolso_unico(self):
        # Creo los datos iniciales
        timestamp = str(int(time.time()))
        
        organizer = self.create_test_user(
            is_organizer=True,
            username=f"org_{timestamp}"
        )
        venue = self.create_test_venue(10) 
        event = self.create_test_event(organizer, venue)
        

        user = self.create_test_user(
            is_organizer=False,
            username=f"usr_{timestamp}",
            password="contra129*",
            email=f"email_{timestamp}@gmail.com"
        )

        # Inicio sesion
        self.login_user(username=user.username, password="contra129*")

        # Creo un ticket y un reembolso
        ticket = self.create_test_ticket(user=user,event=event,quantity=1)
        refundRequest = self.create_refund_request(ticket,user)

        # Verifico que el test haya creado correctamente el reembolso (el test del test valga la redundancia)
        reembolsos = RefundRequest.objects.filter(requester=user)
        print(f"reembolsos: {reembolsos}")        
        self.assertEqual(reembolsos.count(), 1)

        # El usuario va a sus reembolsos y ve que tiene uno activo
        self.page.goto(f"{self.live_server_url}/refund/myrefund/")
        items = self.page.query_selector_all(".list-group-item")
        pendientes = [item for item in items if "Estado: Pendiente" in item.inner_text()]
        reembolsosActivos = len(pendientes)
        print(f"Reembolsos activos antes de interaccion del usuario: {str(reembolsosActivos)}")

        # El usuario va a hacer un reembolso teniendo uno ya activo
        self.page.goto(f"{self.live_server_url}/refund/request/")
        # Rellenar el formulario
        self.page.fill("#ticket_code", str(ticket.ticket_code))
        self.page.select_option("#refund_reason", value="error_compra")
        self.page.fill("#description", "Compre el ticket por error")
        self.page.check("#refundPolicy")

        # Manejar alerta
        alert_message = {}
        def handle_dialog(dialog):
            alert_message['text'] = dialog.message
            dialog.dismiss()
        self.page.on("dialog", handle_dialog)

        # El usuario presiona el boton de enviar 
        self.page.get_by_role("button", name="Enviar solicitud").click()
        self.page.wait_for_timeout(1000)
        
        # Debe saltar un alert que indica que ya hay una solicitud de reembolso pendiente
        print(f"MENSAJE: {alert_message}")
        assert 'text' in alert_message, "Ya hay una solicitud de reembolso pendiente."

        # El usuario va a sus reembolsos y ve que solo hay uno activo, es decir, no se agrego uno nuevo
        self.page.goto(f"{self.live_server_url}/refund/myrefund/")
        items = self.page.query_selector_all(".list-group-item")
        pendientes = [item for item in items if "Estado: Pendiente" in item.inner_text()]
        reembolsosActivos = len(pendientes)
        print(f"Reembolsos activos luego de interaccion del usuario: {str(reembolsosActivos)}")
        assert(reembolsosActivos == 1)
        
