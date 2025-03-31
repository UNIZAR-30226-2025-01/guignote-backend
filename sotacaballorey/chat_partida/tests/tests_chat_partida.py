import json
from django.test import TestCase
from django.urls import reverse
from chat_partida.models import MensajePartida
from partidas.models import Partida, Partida2v2
from usuarios.models import Usuario
from utils.jwt_auth import generar_token  # Ensure token creation is handled correctly

class TestChatMessages(TestCase):
    def setUp(self):
        """
        Setting up the test environment with users and matches.
        Creates 5 1v1 and 5 2v2 matches, and two users for each match.
        """
        # Create users for testing using the custom Usuario model
        self.user1 = Usuario.objects.create(nombre="user1", correo="user1@example.com", contrasegna="password")
        self.user2 = Usuario.objects.create(nombre="user2", correo="user2@example.com", contrasegna="password")
        self.user3 = Usuario.objects.create(nombre="user3", correo="user3@example.com", contrasegna="password")
        self.user4 = Usuario.objects.create(nombre="user4", correo="user4@example.com", contrasegna="password")
        
        self.token_usuario1 = generar_token(self.user1)
        self.token_usuario2 = generar_token(self.user2)
        self.token_usuario3 = generar_token(self.user3)
        self.token_usuario4 = generar_token(self.user4)

        # Create 5 1v1 matches
        self.matches_1v1 = [Partida.objects.create(jugador_1=self.user1, jugador_2=self.user2) for _ in range(5)]
        
        # Create 5 2v2 matches
        self.matches_2v2 = [Partida2v2.objects.create(
            equipo_1_jugador_1=self.user1,
            equipo_1_jugador_2=self.user2,
            equipo_2_jugador_1=self.user3,
            equipo_2_jugador_2=self.user4
        ) for _ in range(5)]

    def send_message_via_view(self, chat_id, user, message, token):
        """
        Helper function to send a message using the view `enviar_mensaje` (via HTTP POST).
        """
        return self.client.post(
            reverse('chat_partida:enviar_mensaje_Partida'),
            json.dumps({
                'chat_id': chat_id,
                'contenido': message
            }), content_type='application/json',
            HTTP_AUTH=token
        )

    def test_send_message_and_store_in_db(self):
        """
        Test sending messages for each match type (1v1 and 2v2) and validate they are stored correctly.
        """
        # Test 1v1 Matches
        for match in self.matches_1v1:
            # Send two messages in the 1v1 match
            message_1 = "Hello, ready for the match!"
            message_2 = "Good luck!"
            response1 = self.send_message_via_view(match.get_chat_id(), self.user1, message_1, self.token_usuario1)
            response2 = self.send_message_via_view(match.get_chat_id(), self.user2, message_2, self.token_usuario2)

            # Validate that the messages were stored in the database
            messages = MensajePartida.objects.filter(chat_id=match.get_chat_id()).order_by('fecha_envio')
            self.assertEqual(messages.count(), 2)
            self.assertEqual(messages[0].contenido, message_1)
            self.assertEqual(messages[1].contenido, message_2)

        # Test 2v2 Matches
        for match in self.matches_2v2:
            # Send two messages in the 2v2 match
            message_1 = "Let's do this!"
            message_2 = "Hope we win!"
            response1 = self.send_message_via_view(match.get_chat_id(), self.user1, message_1, self.token_usuario1)
            response2 = self.send_message_via_view(match.get_chat_id(), self.user4, message_2, self.token_usuario4)

            # Validate that the messages were stored in the database
            messages = MensajePartida.objects.filter(chat_id=match.get_chat_id()).order_by('fecha_envio')
            self.assertEqual(messages.count(), 2)
            self.assertEqual(messages[0].contenido, message_1)
            self.assertEqual(messages[1].contenido, message_2)


