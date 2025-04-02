from django.test import TestCase
from django.urls import reverse
from chat_partida.models import MensajePartida
from partidas.models import Partida, Partida2v2
from usuarios.models import Usuario
from utils.jwt_auth import generar_token
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from sotacaballorey.asgi import application
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
        self.user3 = Usuario.objects.create(nombre="user3", correo="user3@example.com", contrasegna="password")
        self.user4 = Usuario.objects.create(nombre="user4", correo="user4@example.com", contrasegna="password")

        self.token_usuario1 = generar_token(self.user1)
        self.token_usuario2 = generar_token(self.user2)
        self.token_usuario3 = generar_token(self.user3)
        self.token_usuario4 = generar_token(self.user4)

        self.match_2v2 = Partida2v2.objects.create(
            equipo_1_jugador_1=self.user1,
            equipo_1_jugador_2=self.user2,
            equipo_2_jugador_1=self.user3,
            equipo_2_jugador_2=self.user4
        )

   
    async def test_2v2_message_broadcast(self):
        """
        Test that a player in a 2v2 match can send a message and the other 3 players receive it.
        """
        match_id = self.match_2v2.id
        base_url = f"ws://localhost:8000/ws/chat/2v2/{match_id}/"

        # Define connections for all 4 players
        urls_tokens = [
            (f"{base_url}?token={self.token_usuario1}", self.user1),
            (f"{base_url}?token={self.token_usuario2}", self.user2),
            (f"{base_url}?token={self.token_usuario3}", self.user3),
            (f"{base_url}?token={self.token_usuario4}", self.user4),
        ]

        # Create communicators
        communicators = []
        for url, _ in urls_tokens:
            comm = WebsocketCommunicator(application, url)
            connected, _ = await comm.connect()
            self.assertTrue(connected)
            communicators.append(comm)

        # Send message from user1
        message = "Hola equipo desde user1"
        await communicators[0].send_json_to({
            "message": message,
            "user_id": self.user1.id
        })

        # All others should receive it
        for receiver_comm in communicators[1:]:
            response = await receiver_comm.receive_json_from()
            self.assertEqual(response["message"], message)
            self.assertEqual(response["user"], self.user1.nombre)

        # Cleanup
        for comm in communicators:
            await comm.disconnect()