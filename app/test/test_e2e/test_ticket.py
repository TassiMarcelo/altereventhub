import re

from playwright.sync_api import expect

from app.test.test_e2e.base import BaseE2ETest


# Tests para la página de inicio
class TicketModelTest(BaseE2ETest):
    """Tests relacionados con la visualización de la página de inicio"""

    def test_ticket_buy_exceeds_capacity(self):

        # Un organizador crea un evento con espacio = 1
        organizer = self.create_test_user(is_organizer=True)
        venue = self.create_test_venue(1)
        event = self.create_test_event(organizer,venue)  # Crea el primer evento en la DB de testing (ID 1)

        #Un usuario quiere comprar un ticket. va a iniciar sesion y dirigirse al formulario
        user = self.create_test_user(is_organizer=False,username="comprador123",password="contra129*",email="hello@gmail.com")
        self.login_user(username=user.username,password="contra129*") # Usar contraseña plana para no confundir con la hasheada de user.password

        #self.page.screenshot(path="screenshot.png") # Usar screenshot para debug
        

        self.page.goto(f"{self.live_server_url}/ticket/1/form/") # Ir a la compra de entradas para evento con id 1

        # Rellenar el formulario
        self.page.select_option("select[name='type']", "GENERAL")
        self.page.fill("input[name='quantity']", "2")  # Excede la capacidad del evento
        self.page.fill("input[name='card_number']", "1234 5678 9012 3456")
        self.page.fill("input[name='card_expiry']", "12/12")
        self.page.fill("input[name='card_cvv']", "123")
        self.page.check("#terms")

        print(self.page.content())
        

        # Variable para capturar el mensaje del alert
        alert_message = {}

        def handle_dialog(dialog):
            alert_message['text'] = dialog.message
            dialog.dismiss()  # o dialog.accept()

        self.page.on("dialog", handle_dialog)

        # Presionar el botón de comprar
        self.page.click("button:has-text('Comprar')")

        # Esperar un poco para asegurarse de que el alert se dispare
        self.page.wait_for_timeout(1000)

    
        # Verificar que el alert apareció con el mensaje correcto
        assert 'text' in alert_message, "No se disparó ningún alert"
        assert "capacidad" in alert_message['text'].lower() 
