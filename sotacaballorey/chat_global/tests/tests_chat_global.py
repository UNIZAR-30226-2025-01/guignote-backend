from django.test import TestCase
from django.urls import reverse
from usuarios.models import Usuario
from chat_global.models import ChatGlobal
from utils.jwt_auth import generar_token  # Import JWT generation function


class ChatGlobalTestCase(TestCase):

    def setUp(self):
        """Setup before each test - Create users and generate tokens."""
        self.usuario1 = Usuario.objects.create(nombre="Carlos", correo="carlos@example.com", contrasegna="1234")
        self.usuario2 = Usuario.objects.create(nombre="Elena", correo="elena@example.com", contrasegna="1234")
        self.usuario3 = Usuario.objects.create(nombre="David", correo="david@example.com", contrasegna="1234")

        # Generate authentication tokens
        self.token_usuario1 = generar_token(self.usuario1)
        self.token_usuario2 = generar_token(self.usuario2)
        self.token_usuario3 = generar_token(self.usuario3)


    def test_chat_mensajes_en_orden(self):
        """Test that global chat messages are stored and retrieved in chronological order."""

        # 🔹 Send messages between Usuario1 and Usuario2
        mensajes_chat1 = [
            ("Hola, cómo estás?", self.token_usuario1, self.usuario2.id),
            ("Bien, gracias! Y tú?", self.token_usuario2, self.usuario1.id),
            ("Todo bien, listo para jugar?", self.token_usuario1, self.usuario2.id)
        ]

        for mensaje, headers, recipient_id in mensajes_chat1:
            response = self.client.post(
                reverse('chat_global:enviar_mensaje_global', args=[recipient_id, mensaje]),
                HTTP_AUTH=headers
            )
            self.assertEqual(response.status_code, 201)  # Ensure messages are sent successfully

        # 🔹 Send messages between Usuario2 and Usuario3
        mensajes_chat2 = [
            ("Hola David!", self.token_usuario2, self.usuario3.id),
            ("Qué tal, Elena?", self.token_usuario3, self.usuario2.id),
            ("Vamos a jugar después?", self.token_usuario2, self.usuario3.id)
        ]

        for mensaje, headers, recipient_id in mensajes_chat2:
            response = self.client.post(
                reverse('chat_global:enviar_mensaje_global', args=[recipient_id, mensaje]),
                HTTP_AUTH=headers
            )
            self.assertEqual(response.status_code, 201)

        # 🔹 Retrieve messages for Usuario1
        response_chat1 = self.client.get(
            reverse('chat_global:obtener_mensajes_global', args=[self.usuario1.id]),
            HTTP_AUTH=self.token_usuario1
        )
        self.assertEqual(response_chat1.status_code, 200)

        mensajes_recibidos_1 = response_chat1.json()["mensajes"]
        self.assertEqual(len(mensajes_recibidos_1), 3)  # Ensure all 3 messages are retrieved

        # 🔹 Check chronological order for chat 1
        for i in range(len(mensajes_recibidos_1) - 1):
            self.assertLessEqual(mensajes_recibidos_1[i]["timestamp"], mensajes_recibidos_1[i + 1]["timestamp"])

        # 🔹 Retrieve messages for Usuario1
        response_chat2 = self.client.get(
            reverse('chat_global:obtener_mensajes_global', args=[self.usuario2.id]),
            HTTP_AUTH=self.token_usuario2
        )

        self.assertEqual(response_chat2.status_code, 200)

        mensajes_recibidos_2 = response_chat2.json()["mensajes"]
        self.assertEqual(len(mensajes_recibidos_2), 6)  # Should receive 3 from Usuario1 and 3 from Usuario3

        # 🔹 Check chronological order for chat 2
        for i in range(len(mensajes_recibidos_2) - 1):
            self.assertLessEqual(mensajes_recibidos_2[i]["timestamp"], mensajes_recibidos_2[i + 1]["timestamp"])

        # 🔹 Ensure messages do not mix between different users
        self.assertNotEqual(mensajes_recibidos_1, mensajes_recibidos_2)

    def test_mensaje_a_uno_mismo(self):

        mensaje_falso = "Mensaje reflexivo"

        response = self.client.post(
            reverse('chat_global:enviar_mensaje_global', args=[self.usuario3.id, mensaje_falso]),
            HTTP_AUTH=self.token_usuario3
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Cannot send a message to yourself")
        
        
    def test_mirar_mensajes_ajenos(self):

        response = self.client.get(
            reverse('chat_global:obtener_mensajes_global', args=[self.usuario3.id]),
            HTTP_AUTH=self.token_usuario1
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"], "Unauthorized: You can only view your own messages")

