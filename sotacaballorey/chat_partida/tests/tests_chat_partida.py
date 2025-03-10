from django.test import TestCase
from django.urls import reverse
from partidas.models import Partida
from usuarios.models import Usuario
from chat_partida.models import ChatPartida
from utils.jwt_auth import generar_token  # Import JWT generation function


class ChatPartidaTestCase(TestCase):

    def setUp(self):
        """Setup before each test - Create users, matches, and generate tokens."""
        self.jugador1 = Usuario.objects.create(nombre="Carlos", correo="carlos@example.com", contrasegna="1234")
        self.jugador2 = Usuario.objects.create(nombre="Elena", correo="elena@example.com", contrasegna="1234")

        self.jugador3 = Usuario.objects.create(nombre="David", correo="david@example.com", contrasegna="1234")
        self.jugador4 = Usuario.objects.create(nombre="Lucia", correo="lucia@example.com", contrasegna="1234")

        # Create two separate matches
        self.partida1 = Partida.objects.create(jugador_1=self.jugador1, jugador_2=self.jugador2)
        self.partida2 = Partida.objects.create(jugador_1=self.jugador3, jugador_2=self.jugador4)

        # Generate authentication tokens
        self.token_jugador1 = generar_token(self.jugador1)
        self.token_jugador2 = generar_token(self.jugador2)
        self.token_jugador3 = generar_token(self.jugador3)
        self.token_jugador4 = generar_token(self.jugador4)

        # Headers to send authentication tokens
        self.auth_headers_jugador1 = {"HTTP_AUTHORIZATION": f"Bearer {self.token_jugador1}"}
        self.auth_headers_jugador2 = {"HTTP_AUTHORIZATION": f"Bearer {self.token_jugador2}"}
        self.auth_headers_jugador3 = {"HTTP_AUTHORIZATION": f"Bearer {self.token_jugador3}"}
        self.auth_headers_jugador4 = {"HTTP_AUTHORIZATION": f"Bearer {self.token_jugador4}"}

    def test_chat_mensajes_en_orden(self):
        """Test that chat messages are stored and retrieved in chronological order for each match."""

        # 🔹 Send messages to Match 1
        mensajes_partida1 = [
            ("Hola, buena suerte!", self.token_jugador1),
            ("Igualmente!", self.token_jugador2),
            ("Que empiece el juego!", self.token_jugador1)
        ]
        

        for mensaje, headers in mensajes_partida1:
            response = self.client.post(
                reverse('chat_partida:enviar_mensaje_chat', args=[self.partida1.id, mensaje]),
                HTTP_AUTH= headers
            )
            self.assertEqual(response.status_code, 201)  # Ensure messages are sent successfully

        # 🔹 Send messages to Match 2
        mensajes_partida2 = [
            ("Hola, que gane el mejor!", self.token_jugador3),
            ("Seguro, a jugar!", self.token_jugador4),
            ("Vamos allá!", self.token_jugador3)
        ]

        for mensaje, headers in mensajes_partida2:
            response = self.client.post(
                reverse('chat_partida:enviar_mensaje_chat', args=[self.partida2.id, mensaje]),
                HTTP_AUTH=headers
            )
            self.assertEqual(response.status_code, 201)

        # 🔹 Retrieve messages for Match 1
        response_partida1 = self.client.get(reverse('chat_partida:obtener_mensajes_chat', args=[self.partida1.id]), HTTP_AUTH=self.token_jugador1)
        self.assertEqual(response_partida1.status_code, 200)

        mensajes_recibidos_1 = response_partida1.json()["mensajes"]
        self.assertEqual(len(mensajes_recibidos_1), 3)  # Ensure all 3 messages are retrieved

        # 🔹 Check chronological order for Match 1
        for i in range(len(mensajes_recibidos_1) - 1):
            self.assertLessEqual(mensajes_recibidos_1[i]["timestamp"], mensajes_recibidos_1[i + 1]["timestamp"])

        # 🔹 Retrieve messages for Match 2
        response_partida2 = self.client.get(reverse('chat_partida:obtener_mensajes_chat', args=[self.partida2.id]), HTTP_AUTH=self.token_jugador3)
        self.assertEqual(response_partida2.status_code, 200)

        mensajes_recibidos_2 = response_partida2.json()["mensajes"]
        self.assertEqual(len(mensajes_recibidos_2), 3)

        # 🔹 Check chronological order for Match 2
        for i in range(len(mensajes_recibidos_2) - 1):
            self.assertLessEqual(mensajes_recibidos_2[i]["timestamp"], mensajes_recibidos_2[i + 1]["timestamp"])

        # 🔹 Ensure messages do not mix between matches
        self.assertNotEqual(mensajes_recibidos_1, mensajes_recibidos_2)

    def test_mensaje_con_usuario_diferente_al_token(self):
        """Test that sending a message with a different user ID than the token is rejected."""

        mensaje_falso = "Intentando engañar el sistema!"

        response = self.client.post(
            reverse('chat_partida:enviar_mensaje_chat', args=[self.partida1.id, mensaje_falso]),
            HTTP_AUTH=self.auth_headers_jugador1  # Using jugador1's token but sending as jugador2
        )

        self.assertEqual(response.status_code, 401) # Ensure request is unauthorized
        self.assertEqual(response.json()["error"], "Token no válido o ha expirado")
