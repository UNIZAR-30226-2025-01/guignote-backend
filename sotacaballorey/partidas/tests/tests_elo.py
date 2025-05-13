from django.test import TransactionTestCase
from channels.testing import WebsocketCommunicator
from asgiref.sync import async_to_sync, sync_to_async
from sotacaballorey.asgi import application
from utils.jwt_auth import generar_token
from usuarios.models import Usuario
from partidas.models import Partida, JugadorPartida
from partidas.game.utils import db_sync_to_async_save
import json
from django.core.management import call_command

class TestEloUpdates(TransactionTestCase):
    reset_sequences = True

    fixtures = [
            'aspecto_carta/fixtures/initial_data.json',
            'tapete/fixtures/initial_data.json'
        ]
    for fixture in fixtures:
            call_command('loaddata', fixture)

    def setUp(self):
        # Create four users with initial ELOs
        self.user1 = Usuario.objects.create(
            nombre="user1", 
            correo="user1@example.com", 
            contrasegna="password", 
            elo=1200,
            elo_parejas=1200
        )
        self.user1.save()
        self.user2 = Usuario.objects.create(
            nombre="user2", 
            correo="user2@example.com", 
            contrasegna="password", 
            elo=1200,
            elo_parejas=1200
        )
        self.user2.save()
        self.user3 = Usuario.objects.create(
            nombre="user3", 
            correo="user3@example.com", 
            contrasegna="password", 
            elo=1200,
            elo_parejas=1200
        )
        self.user3.save()
        self.user4 = Usuario.objects.create(
            nombre="user4", 
            correo="user4@example.com", 
            contrasegna="password", 
            elo=1200,
            elo_parejas=1200
        )
        self.user4.save()
        
        # Generate JWT tokens
        self.token1 = generar_token(self.user1)
        self.token2 = generar_token(self.user2)
        self.token3 = generar_token(self.user3)
        self.token4 = generar_token(self.user4)
        
        # Create a mock partida
        self.partida = Partida.objects.create(capacidad=2, estado='jugando')
        self.partida.save()
        self.jugador1 = JugadorPartida.objects.create(partida=self.partida, usuario=self.user1, equipo=1)
        self.jugador2 = JugadorPartida.objects.create(partida=self.partida, usuario=self.user2, equipo=2)

        # Create a mock 2v2 partida
        self.partida_2v2 = Partida.objects.create(capacidad=4, estado='jugando')
        self.partida_2v2.save()
        self.jugador1_2v2 = JugadorPartida.objects.create(partida=self.partida_2v2, usuario=self.user1, equipo=1)
        self.jugador2_2v2 = JugadorPartida.objects.create(partida=self.partida_2v2, usuario=self.user2, equipo=1)
        self.jugador3_2v2 = JugadorPartida.objects.create(partida=self.partida_2v2, usuario=self.user3, equipo=2)
        self.jugador4_2v2 = JugadorPartida.objects.create(partida=self.partida_2v2, usuario=self.user4, equipo=2)

    def test_elo_updates_after_match(self):
        async def inner():
            # Connect first user
            url1 = f'/ws/partida/?token={self.token1}&capacidad=2'
            comm1 = WebsocketCommunicator(application, url1)
            connected1, _ = await comm1.connect()
            self.assertTrue(connected1)

            # El usuario 1 recibe mensaje "player_joined" con su info
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'player_joined')
            self.assertTrue(data['data']['usuario']['id'], self.user1.id)

            # Connect second user
            url2 = f'/ws/partida/?token={self.token2}&capacidad=2'
            comm2 = WebsocketCommunicator(application, url2)
            connected2, _ = await comm2.connect()
            self.assertTrue(connected2)

            # El usuario 1 y 2 reciben "player_joined" con la info del jugador 2
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'player_joined')
            self.assertTrue(data['data']['usuario']['id'], self.user2.id)

            msg = await comm2.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'player_joined')
            self.assertTrue(data['data']['usuario']['id'], self.user2.id)

            # La partida se inicia (la sala ya está llena: 2 jugadores)
            # Cada jugador recibe el estado de la partida (equipos, cartas...)
            msg = await comm1.receive_from(timeout=5)
            data_1 = json.loads(msg)
            self.assertTrue(data_1['type'], 'start_game')
            self.assertTrue(data_1['data']['mazo_restante'], 27)
            self.mano_1 = data_1['data']['mis_cartas']

            msg = await comm2.receive_from(timeout=5)
            data_2 = json.loads(msg)
            self.assertTrue(data_2['type'], 'start_game')
            self.assertTrue(data_2['data']['mazo_restante'], 27)
            self.mano_2 = data_2['data']['mis_cartas']

            # Ambos reciben de quién es el turno
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'turn_update')
            self.turno = data['data']['jugador']['id']

            msg = await comm2.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'turn_update')
            turno = data['data']['jugador']['id']
            
            # Set up game state to trigger end game using debug function
            await comm1.send_to(json.dumps({
                'accion': 'debug_set_score',
                'puntos_equipo1': 101,
                'puntos_equipo2': 50
            }))
            
            # Wait for score update confirmation
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertEqual(data["type"], "score_update")

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
            #print(f"Game Status: {state_data['estado']}")
            #print(f"Current Turn: {state_data['turno_actual']}")
            #print(f"Team 1 Points: {state_data['puntos_equipo_1']}")
            #print(f"Team 2 Points: {state_data['puntos_equipo_2']}")
            #print("\nPlayers:")
            #for jugador in state_data['jugadores']:
                #print(f"- {jugador['usuario']['nombre']} (Team {jugador['equipo']}): {len(jugador['cartas_json'])} cards")
            #print(f"\nRemaining Deck: {len(state_data['mazo'])} cards")
            #print(f"Discard Pile: {len(state_data['pozo'])} cards")
            #print("=========================\n")

            # Send debug_finalizar action to trigger game end
            await comm1.send_to(json.dumps({
                "accion": "debug_finalizar"
            }))

            # Wait for game over message specifically
            while True:
                try:
                    msg = await comm1.receive_from(timeout=5)
                    data = json.loads(msg)
                    #print(f"Received message type: {data.get('type')}")  # Print all message types
                    if data.get('type') == 'end_game':
                        break
                except Exception as e:
                    print(f"Error receiving message: {str(e)}")
                    break
            
            #print("Received game over message:", data)

            # Disconnect both users
            try:
                await comm1.disconnect()
            except Exception as e:
                print(f"Error disconnecting comm1: {str(e)}")
            
            try:
                await comm2.disconnect()
            except Exception as e:
                print(f"Error disconnecting comm2: {str(e)}")

            # Refresh users from database using sync_to_async
            await sync_to_async(self.user1.refresh_from_db)()
            await sync_to_async(self.user2.refresh_from_db)()

            # Ganador
            self.assertNotEqual(self.user1.elo, 1200)  # Should have increased
            self.assertEqual(self.user1.victorias, 1)
            self.assertEqual(self.user1.racha_victorias, 1)
            self.assertEqual(self.user1.mayor_racha_victorias, 1)
            self.assertEqual(self.user1.derrotas, 0)

            # Perdedor
            self.assertNotEqual(self.user2.elo, 1200)  # Should have decreased
            self.assertEqual(self.user2.victorias, 0)
            self.assertEqual(self.user2.racha_victorias, 0)
            self.assertEqual(self.user2.mayor_racha_victorias, 0)
            self.assertEqual(self.user2.derrotas, 1)

            self.assertGreater(self.user1.elo, self.user2.elo)  # Winner should have higher ELO

        async_to_sync(inner)()

    def test_elo_updates_after_2v2_match(self):
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

            # La partida se inicia (la sala ya está llena: 4 jugadores)
            # Cada jugador recibe el estado de la partida (equipos, cartas...)
            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data['type'], 'start_game')

            for comm in [comm1, comm2, comm3, comm4]:
                msg = await comm.receive_from(timeout=5)
                data = json.loads(msg)
                self.assertEqual(data['type'], 'turn_update')

            # Set up game state to trigger end game using debug function
            await comm1.send_to(json.dumps({
                'accion': 'debug_set_score',
                'puntos_equipo1': 101,
                'puntos_equipo2': 50
            }))
            
            # Wait for score update confirmation
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertEqual(data["type"], "score_update")

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

            # Send debug_finalizar action to trigger game end
            await comm1.send_to(json.dumps({
                "accion": "debug_finalizar"
            }))

            # Wait for game over message specifically
            while True:
                try:
                    msg = await comm1.receive_from(timeout=5)
                    data = json.loads(msg)
                    if data.get('type') == 'end_game':
                        break
                except Exception as e:
                    print(f"Error receiving message: {str(e)}")
                    break

            # Disconnect all users
            for comm in [comm1, comm2, comm3, comm4]:
                try:
                    await comm.disconnect()
                except Exception as e:
                    print(f"Error disconnecting: {str(e)}")

            # Refresh users from database using sync_to_async
            await sync_to_async(self.user1.refresh_from_db)()
            await sync_to_async(self.user2.refresh_from_db)()
            await sync_to_async(self.user3.refresh_from_db)()
            await sync_to_async(self.user4.refresh_from_db)()

            # Check that ELOs have been updated
            elos = {
                self.user1.elo_parejas,
                self.user2.elo_parejas,
                self.user3.elo_parejas,
                self.user4.elo_parejas
            }
            
            # Should have exactly 2 distinct ELO values
            self.assertEqual(len(elos), 2)
            
            # One pair should be above 1200, one below
            elo_above = max(elos)
            elo_below = min(elos)
            self.assertGreater(elo_above, 1200)
            self.assertLess(elo_below, 1200)
            
            # Count how many users have each ELO
            count_above = sum(1 for user in [self.user1, self.user2, self.user3, self.user4] 
                            if user.elo_parejas == elo_above)
            count_below = sum(1 for user in [self.user1, self.user2, self.user3, self.user4] 
                            if user.elo_parejas == elo_below)
            
            # Should have exactly 2 users with each ELO
            self.assertEqual(count_above, 2)
            self.assertEqual(count_below, 2)

        async_to_sync(inner)()
