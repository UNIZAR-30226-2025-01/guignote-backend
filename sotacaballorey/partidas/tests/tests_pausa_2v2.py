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

class TestPauseFunctionality2v2(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        # Create four users
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
        self.user3 = Usuario.objects.create(
            nombre="user3", 
            correo="user3@example.com", 
            contrasegna="password"
        )
        self.user3.save()
        self.user4 = Usuario.objects.create(
            nombre="user4", 
            correo="user4@example.com", 
            contrasegna="password"
        )
        self.user4.save()
        
        # Generate JWT tokens
        self.token1 = generar_token(self.user1)
        self.token2 = generar_token(self.user2)
        self.token3 = generar_token(self.user3)
        self.token4 = generar_token(self.user4)

        # Make all users friends using the views
        client = Client()
        
        # User1 sends friend requests to others
        for user in [self.user2, self.user3, self.user4]:
            response = client.post(
                reverse('enviar_solicitud_amistad'),
                json.dumps({'destinatario_id': user.id}),
                content_type='application/json',
                headers={'Auth': self.token1}
            )
            self.assertEqual(response.status_code, 201)

        # Others accept the friend requests in order
        for i, (user, token) in enumerate([(self.user2, self.token2), (self.user3, self.token3), (self.user4, self.token4)]):
            response = client.post(
                reverse('aceptar_solicitud_amistad'),
                json.dumps({'solicitud_id': i + 1}),  # Request IDs are 1, 2, 3
                content_type='application/json',
                headers={'Auth': token}
            )
            self.assertEqual(response.status_code, 200)

        # Verify they are all friends
        for user, token in [(self.user1, self.token1), (self.user2, self.token2), 
                          (self.user3, self.token3), (self.user4, self.token4)]:
            response = client.get(
                reverse('obtener_amigos'),
                headers={'Auth': token}
            )
            self.assertEqual(response.status_code, 200)
            amigos = response.json().get('amigos', [])
            if user == self.user1:
                self.assertEqual(len(amigos), 3)  # User1 should have 3 friends
            else:
                self.assertEqual(len(amigos), 1)  # Others should have 1 friend (user1)
                self.assertEqual(amigos[0]['id'], self.user1.id)  # Their friend should be user1


    async def create_websocket_connection(self, user, token, capacidad=4, solo_amigos=False):
        """Helper function to create a WebSocket connection"""
        # Add all custom match parameters
        url = f'/ws/partida/?token={token}&capacidad={capacidad}&es_personalizada={str(solo_amigos).lower()}&solo_amigos={str(solo_amigos).lower()}&tiempo_turno=30&permitir_revueltas=true&reglas_arrastre=true'
        comm = WebsocketCommunicator(application, url)
        connected, _ = await comm.connect()
        self.assertTrue(connected)
        return comm

    def test_2v2_normal_match(self):
        """Test that a 2v2 normal match starts without pausing"""
        async def inner():
            # Connect first user
            url1 = f'/ws/partida/?token={self.token1}&capacidad=4'
            comm1 = WebsocketCommunicator(application, url1)
            connected1, _ = await comm1.connect()
            self.assertTrue(connected1)

            # El usuario 1 recibe mensaje "player_joined" con su info
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'player_joined')
            self.assertTrue(data['data']['usuario']['id'], self.user1.id)

            # Connect second user
            url2 = f'/ws/partida/?token={self.token2}&capacidad=4'
            comm2 = WebsocketCommunicator(application, url2)
            connected2, _ = await comm2.connect()
            self.assertTrue(connected2)

            # All users receive player_joined messages
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data['type'], 'player_joined')

            # Connect third user
            url3 = f'/ws/partida/?token={self.token3}&capacidad=4'
            comm3 = WebsocketCommunicator(application, url3)
            connected3, _ = await comm3.connect()
            self.assertTrue(connected3)

            # Request and wait for debug state
            await comm1.send_to(json.dumps({
                'accion': 'debug_state'
            }))
            
            # Wait for debug state message specifically
            while True:
                msg = await comm1.receive_from(timeout=5)
                data = json.loads(msg)
                if data.get('type') == 'debug_state':
                    break
            
            state_data = data['data']  # Get the nested state data
            #print("\n=== Current Game State ===")
            #print(f"Capacidad: {state_data['capacidad']}")
            #print(f"Game Status: {state_data['estado']}")
            #print(f"Current Turn: {state_data['turno_actual']}")
            #print(f"Team 1 Points: {state_data['puntos_equipo_1']}")
            #print(f"Team 2 Points: {state_data['puntos_equipo_2']}")
            #print("\nPlayers:")
            #for jugador in state_data['jugadores']:
            #    print(f"- {jugador['usuario']['nombre']} (Team {jugador['equipo']}): {len(jugador['cartas_json'])} cards")
            #print(f"\nRemaining Deck: {len(state_data['mazo'])} cards")
            #print(f"Discard Pile: {len(state_data['pozo'])} cards")
            #print("=========================\n")

            # All users receive player_joined messages
            for comm in [comm1, comm2, comm3]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data['type'], 'player_joined')

            # Connect fourth user
            url4 = f'/ws/partida/?token={self.token4}&capacidad=4'
            comm4 = WebsocketCommunicator(application, url4)
            connected4, _ = await comm4.connect()
            self.assertTrue(connected4)

            # All users receive player_joined messages
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data['type'], 'player_joined')

            # Wait for start_game messages for all users
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "start_game")

            # Wait for turn_update messages for all users
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "turn_update")

            # First player requests pause
            pausa = {'accion': 'pausa'}
            await comm1.send_to(text_data=json.dumps(pausa))

            # All players should receive pause request message
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # Second player requests pause
            pausa = {'accion': 'pausa'}
            await comm2.send_to(text_data=json.dumps(pausa))

            # All players should receive pause request message
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # Third player requests pause
            pausa = {'accion': 'pausa'}
            await comm3.send_to(text_data=json.dumps(pausa))

            # All players should receive pause request message
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # Fourth player requests pause
            pausa = {'accion': 'pausa'}
            await comm4.send_to(text_data=json.dumps(pausa))

            # All players should receive pause request message
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # All players should receive final pause message
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "all_pause")
                self.assertEqual(data["data"]["message"], "La partida ha sido pausada por acuerdo de todos los jugadores.")

        async_to_sync(inner)()

    def test_cancel_pause_2v2(self):
        """Test that a player can cancel their pause request in a 2v2 match"""
        async def inner():
            # Connect first user
            url1 = f'/ws/partida/?token={self.token1}&capacidad=4'
            comm1 = WebsocketCommunicator(application, url1)
            connected1, _ = await comm1.connect()
            self.assertTrue(connected1)

            # El usuario 1 recibe mensaje "player_joined" con su info
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'player_joined')
            self.assertTrue(data['data']['usuario']['id'], self.user1.id)

            # Connect second user
            url2 = f'/ws/partida/?token={self.token2}&capacidad=4'
            comm2 = WebsocketCommunicator(application, url2)
            connected2, _ = await comm2.connect()
            self.assertTrue(connected2)

            # All users receive player_joined messages
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data['type'], 'player_joined')

            # Connect third user
            url3 = f'/ws/partida/?token={self.token3}&capacidad=4'
            comm3 = WebsocketCommunicator(application, url3)
            connected3, _ = await comm3.connect()
            self.assertTrue(connected3)

            # All users receive player_joined messages
            for comm in [comm1, comm2, comm3]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data['type'], 'player_joined')

            # Connect fourth user
            url4 = f'/ws/partida/?token={self.token4}&capacidad=4'
            comm4 = WebsocketCommunicator(application, url4)
            connected4, _ = await comm4.connect()
            self.assertTrue(connected4)

            # All users receive player_joined messages
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data['type'], 'player_joined')

            # Wait for start_game messages for all users
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "start_game")

            # Wait for turn_update messages for all users
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "turn_update")

            # First player requests pause
            pausa = {'accion': 'pausa'}
            await comm1.send_to(text_data=json.dumps(pausa))

            # All players should receive pause request message
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # First player cancels pause
            cancel_pausa = {'accion': 'anular_pausa'}
            await comm1.send_to(text_data=json.dumps(cancel_pausa))

            # All players should receive resume message
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "resume")

            # Now test that we can pause again after resuming
            # First player requests pause again
            pausa = {'accion': 'pausa'}
            await comm1.send_to(text_data=json.dumps(pausa))

            # All players should receive pause request message
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # Second player requests pause
            pausa = {'accion': 'pausa'}
            await comm2.send_to(text_data=json.dumps(pausa))

            # All players should receive pause request message
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # Third player requests pause
            pausa = {'accion': 'pausa'}
            await comm3.send_to(text_data=json.dumps(pausa))

            # All players should receive pause request message
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # Fourth player requests pause
            pausa = {'accion': 'pausa'}
            await comm4.send_to(text_data=json.dumps(pausa))

            # All players should receive pause request message
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # All players should receive final pause message
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "all_pause")
                self.assertEqual(data["data"]["message"], "La partida ha sido pausada por acuerdo de todos los jugadores.")

        async_to_sync(inner)()

    def test_2v2_friend_match_single_pause(self):
        tracemalloc.start()
        """Test that in a 2v2 friend-only match, a single player's pause request pauses the game immediately"""
        async def inner():
            # Connect first user in friend-only mode with all custom parameters
            comm1 = await self.create_websocket_connection(self.user1, self.token1, capacidad=4, solo_amigos=True)

            # El usuario 1 recibe mensaje "player_joined" con su info
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'player_joined')
            self.assertTrue(data['data']['usuario']['id'], self.user1.id)

            # Connect second user with same parameters
            comm2 = await self.create_websocket_connection(self.user2, self.token2, capacidad=4, solo_amigos=True)

            # All users receive player_joined messages
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "player_joined")

            # Connect third user with same parameters
            comm3 = await self.create_websocket_connection(self.user3, self.token3, capacidad=4, solo_amigos=True)

            # All users receive player_joined messages
            for comm in [comm1, comm2, comm3]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "player_joined")

            # Connect fourth user with same parameters
            comm4 = await self.create_websocket_connection(self.user4, self.token4, capacidad=4, solo_amigos=True)

            # All users receive player_joined messages
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "player_joined")

            # Wait for start_game messages for all users
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "start_game")

            # Wait for turn_update messages for all users
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "turn_update")

            # First player requests pause
            pausa = {'accion': 'pausa'}
            await comm1.send_to(text_data=json.dumps(pausa))

            # All players should receive pause request message
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # Request and wait for debug state
            await comm1.send_to(json.dumps({
                'accion': 'debug_state'
            }))
            
            # Wait for debug state message specifically
            while True:
                msg = await comm1.receive_from(timeout=5)
                data = json.loads(msg)
                if data.get('type') == 'debug_state':
                    break
            
            #state_data = data['data']  # Get the nested state data
            #print("\n=== Current Game State ===")
            #print(f"Capacidad: {state_data['capacidad']}")
            #print(f"Game Status: {state_data['estado']}")
            #print(f"Current Turn: {state_data['turno_actual']}")
            #print(f"Team 1 Points: {state_data['puntos_equipo_1']}")
            #print(f"Team 2 Points: {state_data['puntos_equipo_2']}")
            #print("\nPlayers:")
            #for jugador in state_data['jugadores']:
            #    print(f"- {jugador['usuario']['nombre']} (Team {jugador['equipo']}): {len(jugador['cartas_json'])} cards")
            #print(f"\nRemaining Deck: {len(state_data['mazo'])} cards")
            #print(f"Discard Pile: {len(state_data['pozo'])} cards")
            #print(f"Solo Amigos: {state_data['solo_amigos']}")
            #print("=========================\n")

            # All players should receive final pause message immediately (no need for other players' requests)
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "all_pause")

            # Disconnect all users
            for comm in [comm1, comm2, comm3, comm4]:
                try:
                    await comm.disconnect()
                except Exception as e:
                    print(f"Error disconnecting: {str(e)}")

        async_to_sync(inner)()

    def test_2v2_normal_match_reconnect(self):
        """Test that a 2v2 normal match can be reconnected after pausing"""
        async def inner():
            # Connect first user
            url1 = f'/ws/partida/?token={self.token1}&capacidad=4'
            comm1 = WebsocketCommunicator(application, url1)
            connected1, _ = await comm1.connect()
            self.assertTrue(connected1)

            # El usuario 1 recibe mensaje "player_joined" con su info
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'player_joined')
            self.assertTrue(data['data']['usuario']['id'], self.user1.id)
            match_id = data["data"]["partida_id"]

            # Connect second user
            url2 = f'/ws/partida/?token={self.token2}&capacidad=4'
            comm2 = WebsocketCommunicator(application, url2)
            connected2, _ = await comm2.connect()
            self.assertTrue(connected2)

            # All users receive player_joined messages
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data['type'], 'player_joined')

            # Connect third user
            url3 = f'/ws/partida/?token={self.token3}&capacidad=4'
            comm3 = WebsocketCommunicator(application, url3)
            connected3, _ = await comm3.connect()
            self.assertTrue(connected3)

            # All users receive player_joined messages
            for comm in [comm1, comm2, comm3]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data['type'], 'player_joined')

            # Connect fourth user
            url4 = f'/ws/partida/?token={self.token4}&capacidad=4'
            comm4 = WebsocketCommunicator(application, url4)
            connected4, _ = await comm4.connect()
            self.assertTrue(connected4)

            # All users receive player_joined messages
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data['type'], 'player_joined')

            # Wait for start_game messages for all users
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "start_game")

            # Wait for turn_update messages for all users
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "turn_update")

            # First player requests pause
            pausa = {'accion': 'pausa'}
            await comm1.send_to(text_data=json.dumps(pausa))

            # All players should receive pause request message
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # Second player requests pause
            pausa = {'accion': 'pausa'}
            await comm2.send_to(text_data=json.dumps(pausa))

            # All players should receive pause request message
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # Third player requests pause
            pausa = {'accion': 'pausa'}
            await comm3.send_to(text_data=json.dumps(pausa))

            # All players should receive pause request message
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # Fourth player requests pause
            pausa = {'accion': 'pausa'}
            await comm4.send_to(text_data=json.dumps(pausa))

            # All players should receive pause request message
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "pause")

            # All players should receive final pause message
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "all_pause")
                self.assertEqual(data["data"]["message"], "La partida ha sido pausada por acuerdo de todos los jugadores.")

            # Disconnect all users
            for comm in [comm1, comm2, comm3, comm4]:
                await comm.disconnect()


            # Reconnect all users
            for user, token in [(self.user1, self.token1), (self.user2, self.token2), 
                              (self.user3, self.token3), (self.user4, self.token4)]:
                url = f'/ws/partida/?token={token}&id_partida={match_id}&capacidad=4'
                comm = WebsocketCommunicator(application, url)
                connected, _ = await comm.connect()
                self.assertTrue(connected)


            # El usuario 1 recibe mensaje "player_joined" con su info
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'player_joined')
            self.assertTrue(data['data']['usuario']['id'], self.user1.id)
            
            # All users receive player_joined messages
            for comm in [comm1, comm2]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data['type'], 'player_joined')

            # All users receive player_joined messages
            for comm in [comm1, comm2, comm3]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data['type'], 'player_joined')

            # All users receive player_joined messages
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data['type'], 'player_joined')

            # Verify all users receive start_game messages
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "start_game")

            # Verify all users receive turn_update messages
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data["type"], "turn_update")

        async_to_sync(inner)()