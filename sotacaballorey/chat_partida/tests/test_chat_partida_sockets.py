from django.test import TestCase
from django.urls import reverse
from chat_partida.models import MensajePartida, Chat_partida as Chat
from partidas.models import Partida
from usuarios.models import Usuario
from utils.jwt_auth import generar_token
from channels.testing import WebsocketCommunicator
from chat_partida.chatConsumer import ChatConsumer
from django.conf import settings
import json
import asyncio

class TestWebSocketCommunication(TestCase):

    def setUp(self):
        """
        Setting up the test environment with users and a 1v1 match.
        Creates two users and a 1v1 match between them.
        """
        # Create users for testing using the custom Usuario model
        self.user1 = Usuario.objects.create(nombre="user1", correo="user1@example.com", contrasegna="password")
        self.user2 = Usuario.objects.create(nombre="user2", correo="user2@example.com", contrasegna="password")

        self.token_usuario1 = generar_token(self.user1)
        self.token_usuario2 = generar_token(self.user2)

        # Create a 1v1 match
        self.match = Partida.objects.create(jugador_1=self.user1, jugador_2=self.user2)

        # Create a chat for the match
        self.chat = Chat.objects.create()
        self.match.chat = self.chat
        self.match.save()

        # Add participants to the chat
        self.chat.add_participant(self.user1)
        self.chat.add_participant(self.user2)


    async def test_message_send_and_receive(self):
        """
        Test that a player can send a message via WebSocket and the other player receives it.
        """
        # Connect both players to the WebSocket

        # Base URL for the WebSocket (adjust according to your actual host and port)
        host = "localhost"  # Typically, this will be 'localhost' or your domain
        port = 8000  # Example if you have a custom port defined in your settings (or default to 8000)
        print(host)
        print(port)
        # Construct the WebSocket URL for a 1v1 match (Partida)
        url1 = f"ws://{host}:{port}/ws/chat/1v1/{self.match.id}/?token={self.token_usuario1}"
        url2 = f"ws://{host}:{port}/ws/chat/1v1/{self.match.id}/?token={self.token_usuario2}"


        # Create WebSocket communicators for both players using their token for authentication
        


        communicator1 =  WebsocketCommunicator(ChatConsumer.as_asgi(), url1)
        connected1, subprotocol1 = await communicator1.connect()
        communicator2 =  WebsocketCommunicator(ChatConsumer.as_asgi(), url2)
        connected2, subprotocol2 = await communicator2.connect()


        # Player 1 sends a message to the chat via WebSocket
        message = "Hello from user1!"
        await communicator1.send_json_to({
            "message": message,
            "user_id": self.user1.id
        })

        # Player 2 should receive the message
        response = await communicator2.receive_json_from()

        # Assert that Player 2 receives the correct message
        self.assertEqual(response["message"], message)
        self.assertEqual(response["user"], self.user1.nombre)

        # Close the connections
        await communicator1.disconnect()
        await communicator2.disconnect()
