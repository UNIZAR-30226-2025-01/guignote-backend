from django.test import TestCase
from django.urls import reverse
from partidas.models import Partida2v2
from usuarios.models import Usuario
from chat_partida.models import ChatPartidaParejas  # Updated model name
from utils.jwt_auth import generar_token  # Import JWT generation function


class ChatPartidaParejasTestCase(TestCase):

    def setUp(self):
        """Setup before each test - Create users, matches, and generate tokens."""
        self.jugadores = [
            Usuario.objects.create(nombre=f"Jugador{i}", correo=f"jugador{i}@example.com", contrasegna="1234")
            for i in range(1, 9)  # Create 8 players
        ]

        # Create two separate 2v2 matches
        self.partida1 = Partida2v2.objects.create(
            equipo_1_jugador_1=self.jugadores[0], equipo_1_jugador_2=self.jugadores[1],
            equipo_2_jugador_1=self.jugadores[2], equipo_2_jugador_2=self.jugadores[3]
        )

        self.partida2 = Partida2v2.objects.create(
            equipo_1_jugador_1=self.jugadores[4], equipo_1_jugador_2=self.jugadores[5],
            equipo_2_jugador_1=self.jugadores[6], equipo_2_jugador_2=self.jugadores[7]
        )

        # Generate authentication tokens
        self.tokens = {jugador: generar_token(jugador) for jugador in self.jugadores}


    def test_chat_mensajes_en_orden_parejas(self):
        """Test that chat messages are stored and retrieved in chronological order for each 2v2 match."""

        # 🔹 Send messages to Match 1
        mensajes_partida1 = [
            ("Vamos equipo!", self.tokens[self.jugadores[0]]),
            ("Démoslo todo!", self.tokens[self.jugadores[1]]),
            ("Suerte a todos!", self.tokens[self.jugadores[2]]),
            ("Que gane el mejor!", self.tokens[self.jugadores[3]])
        ]

        for mensaje, headers in mensajes_partida1:
            response = self.client.post(
                reverse('chat_partida:enviar_mensaje_chat_parejas', args=[self.partida1.id, mensaje]),
                HTTP_AUTH=headers
            )
            
            self.assertEqual(response.status_code, 201)  # Ensure messages are sent successfully

        # 🔹 Send messages to Match 2
        mensajes_partida2 = [
            ("Hola equipo!", self.tokens[self.jugadores[4]]),
            ("Listos para jugar!", self.tokens[self.jugadores[5]]),
            ("A por todas!", self.tokens[self.jugadores[6]]),
            ("Buena suerte!", self.tokens[self.jugadores[7]])
        ]

        for mensaje, headers in mensajes_partida2:
            response = self.client.post(
                reverse('chat_partida:enviar_mensaje_chat_parejas', args=[self.partida2.id, mensaje]),
                HTTP_AUTH=headers
            )
            self.assertEqual(response.status_code, 201)

        # 🔹 Retrieve messages for Match 1
        response_partida1 = self.client.get(
            reverse('chat_partida:obtener_mensajes_chat_parejas', args=[self.partida1.id]), 
            HTTP_AUTH=self.tokens[self.jugadores[0]]
        )
        self.assertEqual(response_partida1.status_code, 200)

        mensajes_recibidos_1 = response_partida1.json()["mensajes"]
        self.assertEqual(len(mensajes_recibidos_1), 4)  # Ensure all 4 messages are retrieved

        # 🔹 Check chronological order for Match 1
        for i in range(len(mensajes_recibidos_1) - 1):
            self.assertLessEqual(mensajes_recibidos_1[i]["timestamp"], mensajes_recibidos_1[i + 1]["timestamp"])

        # 🔹 Retrieve messages for Match 2
        response_partida2 = self.client.get(
            reverse('chat_partida:obtener_mensajes_chat_parejas', args=[self.partida2.id]), 
            HTTP_AUTH=self.tokens[self.jugadores[4]]
        )
        self.assertEqual(response_partida2.status_code, 200)

        mensajes_recibidos_2 = response_partida2.json()["mensajes"]
        self.assertEqual(len(mensajes_recibidos_2), 4)

        # 🔹 Check chronological order for Match 2
        for i in range(len(mensajes_recibidos_2) - 1):
            self.assertLessEqual(mensajes_recibidos_2[i]["timestamp"], mensajes_recibidos_2[i + 1]["timestamp"])

        # 🔹 Ensure messages do not mix between matches
        self.assertNotEqual(mensajes_recibidos_1, mensajes_recibidos_2)

