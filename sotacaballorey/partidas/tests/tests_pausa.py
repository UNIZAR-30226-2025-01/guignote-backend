from django.test import TransactionTestCase, AsyncClient
from channels.testing import WebsocketCommunicator
from asgiref.sync import async_to_sync, sync_to_async
from sotacaballorey.asgi import application
from utils.jwt_auth import generar_token
from usuarios.models import Usuario
from partidas.models import Partida, JugadorPartida
from partidas.game.utils import db_sync_to_async_save
from django.urls import reverse
import json
from django.test import Client
import tracemalloc

class TestPauseFunctionality(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        # Create two users
        self.user1 = Usuario.objects.create(
            nombre="user1", 
            correo="user1@example.com", 
            contrasegna="password"
        )
        self.user1.save()
        self.user2 = Usuario.objects.create(
            nombre="user2", 
            correo="user2@example.com", 
            contrasegna="password"
        )
        self.user2.save()
        
        # Generate JWT tokens
        self.token1 = generar_token(self.user1)
        self.token2 = generar_token(self.user2)

        # Make user1 and user2 friends using the views
        client = Client()
        
        # User1 sends friend request to user2
        response =  client.post(
            reverse('enviar_solicitud_amistad'),
            json.dumps({'destinatario_id': self.user2.id}),
            content_type='application/json',
            headers={'Auth': self.token1}
        )
        self.assertEqual(response.status_code, 201)

        # User2 accepts the friend request
        response = client.post(
            reverse('aceptar_solicitud_amistad'),
            json.dumps({'solicitud_id': 1}),  # First request will have ID 1
            content_type='application/json',
            headers={'Auth': self.token2}
        )
        self.assertEqual(response.status_code, 200)

        # Verify they are friends
        response = client.get(
            reverse('obtener_amigos'),
            headers={'Auth': self.token1}
        )
        self.assertEqual(response.status_code, 200)
        amigos = response.json().get('amigos', [])
        self.assertTrue(any(amigo['id'] == self.user2.id for amigo in amigos))

    async def create_websocket_connection(self, user, token, capacidad=2, solo_amigos=False):
        """Helper function to create a WebSocket connection"""
        url = f'/ws/partida/?token={token}&capacidad={capacidad}&solo_amigos={str(solo_amigos).lower()}'
        comm = WebsocketCommunicator(application, url)
        connected, _ = await comm.connect()
        self.assertTrue(connected)
        return comm

    def test_1v1_normal_match(self):
        """Test that a 1v1 normal match starts without pausing"""
        async def inner():
            # Connect both users
            comm1 = await self.create_websocket_connection(self.user1, self.token1)

            # El usuario 1 recibe mensaje "player_joined" con su info
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'player_joined')
            self.assertTrue(data['data']['usuario']['id'], self.user1.id)

            comm2 = await self.create_websocket_connection(self.user2, self.token2)

            # Wait for player_joined messages for both users
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "player_joined")

            # Wait for start_game messages for both users
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "start_game")

            # Wait for turn_update messages for both users
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "turn_update")

            # First player requests pause
            pausa = {'accion': 'pausa'}
            await comm1.send_to(text_data=json.dumps(pausa))

            # Both players should receive pause request message
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # Second player requests pause
            pausa = {'accion': 'pausa'}
            await comm2.send_to(text_data=json.dumps(pausa))

            # Both players should receive pause request message
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # Both players should receive final pause message
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "all_pause")
                self.assertEqual(data["data"]["message"], "La partida ha sido pausada por acuerdo de todos los jugadores.")

        async_to_sync(inner)()

    def test_cancel_pause(self):
        """Test that a player can cancel their pause request"""
        async def inner():
            # Connect both users
            comm1 = await self.create_websocket_connection(self.user1, self.token1)

            # El usuario 1 recibe mensaje "player_joined" con su info
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'player_joined')
            self.assertTrue(data['data']['usuario']['id'], self.user1.id)

            comm2 = await self.create_websocket_connection(self.user2, self.token2)

            # Wait for player_joined messages for both users
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "player_joined")

            # Wait for start_game messages for both users
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "start_game")

            # Wait for turn_update messages for both users
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "turn_update")

            # First player requests pause
            pausa = {'accion': 'pausa'}
            await comm1.send_to(text_data=json.dumps(pausa))

            # Both players should receive pause request message
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # First player cancels pause
            cancel_pausa = {'accion': 'anular_pausa'}
            await comm1.send_to(text_data=json.dumps(cancel_pausa))

            # Both players should receive resume message
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "resume")

            # Now test that we can pause again after resuming
            # First player requests pause again
            pausa = {'accion': 'pausa'}
            await comm1.send_to(text_data=json.dumps(pausa))

            # Both players should receive pause request message
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # Second player requests pause
            pausa = {'accion': 'pausa'}
            await comm2.send_to(text_data=json.dumps(pausa))

            # Both players should receive pause request message
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # Both players should receive final pause message
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "all_pause")
                self.assertEqual(data["data"]["message"], "La partida ha sido pausada por acuerdo de todos los jugadores.")

        async_to_sync(inner)()

    def test_friend_match_single_pause(self):
        tracemalloc.start()
        """Test that in a friend-only match, a single player's pause request pauses the game immediately"""
        async def inner():
            # Connect first user in friend-only mode
            comm1 = await self.create_websocket_connection(self.user1, self.token1, solo_amigos=True)

            # El usuario 1 recibe mensaje "player_joined" con su info
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'player_joined')
            self.assertTrue(data['data']['usuario']['id'], self.user1.id)

            # Get the match ID from the friends rooms endpoint
            client = AsyncClient()
            url = reverse('salas_disponibles_amigos')
            response = await client.get(url, headers={'Auth': self.token2})
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(len(data['salas']) > 0)
            match_id = data['salas'][0]['id']

            # Connect second user using the match ID
            url2 = f'/ws/partida/?token={self.token2}&id_partida={match_id}'
            comm2 = WebsocketCommunicator(application, url2)
            connected2, _ = await comm2.connect()
            self.assertTrue(connected2)

            # Wait for player_joined messages for both users
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "player_joined")

            # Wait for start_game messages for both users
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "start_game")

            # Wait for turn_update messages for both users
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "turn_update")

            # First player requests pause
            pausa = {'accion': 'pausa'}
            await comm1.send_to(text_data=json.dumps(pausa))

            # Both players should receive pause request message
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # Both players should receive final pause message immediately (no need for second player's request)
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "all_pause")
                self.assertEqual(data["data"]["message"], "La partida ha sido pausada por ser una partida entre amigos.")

        async_to_sync(inner)()

    def test_1v1_normal_match_reconnect(self):
        """Test that a 1v1 normal match starts without pausing"""
        async def inner():
            # Connect both users
            comm1 = await self.create_websocket_connection(self.user1, self.token1)

            # El usuario 1 recibe mensaje "player_joined" con su info
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'player_joined')
            self.assertTrue(data['data']['usuario']['id'], self.user1.id)

            comm2 = await self.create_websocket_connection(self.user2, self.token2)

            # Wait for player_joined messages for both users
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "player_joined")

            # Wait for start_game messages for both users
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "start_game")

            # Wait for turn_update messages for both users
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "turn_update")

            # First player requests pause
            pausa = {'accion': 'pausa'}
            await comm1.send_to(text_data=json.dumps(pausa))

            # Both players should receive pause request message
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # Second player requests pause
            pausa = {'accion': 'pausa'}
            await comm2.send_to(text_data=json.dumps(pausa))

            # Both players should receive pause request message
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # Both players should receive final pause message
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "all_pause")
                self.assertEqual(data["data"]["message"], "La partida ha sido pausada por acuerdo de todos los jugadores.")

            # Disconnect both users
            await comm1.disconnect()
            await comm2.disconnect()

            # Get reconnectable rooms for both users
            client = AsyncClient()
            
            # Check user1's reconnectable rooms
            response = await client.get(
                reverse('salas_pausadas'),
                headers={'Auth': self.token1}
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(len(data['salas']) > 0)
            match_id = data['salas'][0]['id']

            # Reconnect user1
            url1 = f'/ws/partida/?token={self.token1}&id_partida={match_id}'
            comm1 = WebsocketCommunicator(application, url1)
            connected1, _ = await comm1.connect()
            self.assertTrue(connected1)

            # El usuario 1 recibe mensaje "player_joined" con su info
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'player_joined')
            self.assertTrue(data['data']['usuario']['id'], self.user1.id)

            # Check user2's reconnectable rooms
            response = await client.get(
                reverse('salas_pausadas'),
                headers={'Auth': self.token2}
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(len(data['salas']) > 0)
            self.assertEqual(data['salas'][0]['id'], match_id)  # Should be the same match

            # Reconnect user2
            url2 = f'/ws/partida/?token={self.token2}&id_partida={match_id}'
            comm2 = WebsocketCommunicator(application, url2)
            connected2, _ = await comm2.connect()
            self.assertTrue(connected2)

            # Verify both users receive player_joined messages
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "player_joined")

            # Verify both users receive start_game messages
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "start_game")

            # Verify both users receive turn_update messages
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "turn_update")

        async_to_sync(inner)()