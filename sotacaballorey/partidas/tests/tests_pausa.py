from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from sotacaballorey.asgi import application
from utils.jwt_auth import generar_token
from asgiref.sync import async_to_sync
from usuarios.models import Usuario
import json
from django.core.management import call_command

class TestPauseFunctionality(TransactionTestCase):
    reset_sequences = True

    fixtures = [
            'aspecto_carta/fixtures/initial_data.json',
            'tapete/fixtures/initial_data.json'
        ]
    for fixture in fixtures:
            call_command('loaddata', fixture)

    def setUp(self):
        # Create two users
        self.user1 = Usuario.objects.create(
            nombre="user1", 
            correo="user1@example.com", 
            contrasegna="password"
        )
        self.user2 = Usuario.objects.create(
            nombre="user2", 
            correo="user2@example.com", 
            contrasegna="password"
        )

        # Generate JWT tokens
        self.token1 = generar_token(self.user1)
        self.token2 = generar_token(self.user2)

        # Make user1 and user2 friends
        self.user1.amigos.add(self.user2)

    async def create_websocket_connection(self, token, capacidad=2, solo_amigos=False):
        """Helper function to create a WebSocket connection"""
        url = f'/ws/partida/?token={token}&capacidad={capacidad}&es_personalizada={solo_amigos}&solo_amigos={str(solo_amigos).lower()}'
        comm = WebsocketCommunicator(application, url)
        connected, _ = await comm.connect()
        self.assertTrue(connected)
        return comm

    def test_1v1_normal_match(self):
        """Test that a 1v1 normal match starts without pausing"""
        async def inner():

            # Se conecta el usuario 1
            comm1 = await self.create_websocket_connection(self.token1)
            
            # El usuario 1 recibe mensaje "player_joined" con su info
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'player_joined')
            self.assertTrue(data['data']['usuario']['id'], self.user1.id)

            # Se conecta el usuario 2
            comm2 = await self.create_websocket_connection(self.token2)

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
            comm1 = await self.create_websocket_connection(self.token1)

            # El usuario 1 recibe mensaje "player_joined" con su info
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'player_joined')
            self.assertTrue(data['data']['usuario']['id'], self.user1.id)

            # Se conecta el usuario 2
            comm2 = await self.create_websocket_connection(self.token2)

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
        """Test that in a friend-only match, a single player's pause request pauses the game immediately"""
        async def inner():
            # Connect first user in friend-only mode
            comm1 = await self.create_websocket_connection(self.token1, solo_amigos=True)

            # El usuario 1 recibe mensaje "player_joined" con su info
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'player_joined')
            self.assertTrue(data['data']['usuario']['id'], self.user1.id)

            # Connect second user using the match ID
            comm2 = await self.create_websocket_connection(self.token2, solo_amigos=True)

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

        async_to_sync(inner)()

    def test_1v1_normal_match_reconnect(self):
        """Test that a 1v1 normal match starts without pausing"""
        async def inner():
            # Connect both users
            comm1 = await self.create_websocket_connection(self.token1)
            
            # El usuario 1 recibe mensaje "player_joined" con su info
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'player_joined')
            self.assertTrue(data['data']['usuario']['id'], self.user1.id)
            match_id = data['data']['partida_id']

            comm2 = await self.create_websocket_connection(self.token2)

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

        async_to_sync(inner)()