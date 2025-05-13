import json
from django.test import TestCase, Client
from chat_partida.models import Chat_partida, MensajePartida
from partidas.models import Partida, JugadorPartida
from usuarios.models import Usuario
from utils.jwt_auth import generar_token
from django.urls import reverse
from django.core.management import call_command

class TestChatMessages(TestCase):

    fixtures = [
            'aspecto_carta/fixtures/initial_data.json',
            'tapete/fixtures/initial_data.json'
        ]
    for fixture in fixtures:
            call_command('loaddata', fixture)

    def setUp(self):
        """
        Setting up the test environment with users and matches.
        Creates 5 1v1 and 5 2v2 matches, and two users for each match.
        """
        self.client = Client()

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
        self.matches_1v1 = []
        for _ in range(5):
            partida = Partida.objects.create(capacidad=2)
            JugadorPartida.objects.create(partida=partida, usuario=self.user1, equipo=1)
            JugadorPartida.objects.create(partida=partida, usuario=self.user2, equipo=2)
            self.matches_1v1.append(partida)
        
        # Create 5 2v2 matches
        self.matches_2v2 = []
        for _ in range(5):
            partida = Partida.objects.create(capacidad=4)
            JugadorPartida.objects.create(partida=partida, usuario=self.user1, equipo=1)
            JugadorPartida.objects.create(partida=partida, usuario=self.user2, equipo=1)
            JugadorPartida.objects.create(partida=partida, usuario=self.user3, equipo=2)
            JugadorPartida.objects.create(partida=partida, usuario=self.user4, equipo=2)
            self.matches_2v2.append(partida)

    def send_message_via_view(self, chat_id, message, token):
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
            match.chat.add_participant(self.user1)
            match.chat.add_participant(self.user2)

            # Send two messages in the 1v1 match

            message_1 = "Hello, ready for the match!"
            message_2 = "Good luck!"
            response1 = self.send_message_via_view(match.get_chat_id(), message_1, self.token_usuario1)
            response2 = self.send_message_via_view(match.get_chat_id(), message_2, self.token_usuario2)

            # Validate that the messages were stored in the database
            messages = MensajePartida.objects.filter(chat_id=match.get_chat_id()).order_by('fecha_envio')
            self.assertEqual(messages.count(), 2)
            self.assertEqual(messages[0].contenido, message_1)
            self.assertEqual(messages[1].contenido, message_2)

        # Test 2v2 Matches
        for match in self.matches_2v2:
            match.chat.add_participant(self.user1)
            match.chat.add_participant(self.user2)
            match.chat.add_participant(self.user3)
            match.chat.add_participant(self.user4)

            # Send two messages in the 2v2 match
            message_1 = "Let's do this!"
            message_2 = "Hope we win!"
            response1 = self.send_message_via_view(match.get_chat_id(), message_1, self.token_usuario1)
            response2 = self.send_message_via_view(match.get_chat_id(), message_2, self.token_usuario4)

            # Validate that the messages were stored in the database
            messages = MensajePartida.objects.filter(chat_id=match.get_chat_id()).order_by('fecha_envio')
            self.assertEqual(messages.count(), 2)
            self.assertEqual(messages[0].contenido, message_1)
            self.assertEqual(messages[1].contenido, message_2)


