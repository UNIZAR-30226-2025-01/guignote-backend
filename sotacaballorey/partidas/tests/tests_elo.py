from django.test import TransactionTestCase
from channels.testing import WebsocketCommunicator
from asgiref.sync import async_to_sync, sync_to_async
from sotacaballorey.asgi import application
from utils.jwt_auth import generar_token
from usuarios.models import Usuario
from partidas.models import Partida, JugadorPartida
from partidas.game.utils import db_sync_to_async_save
import json

class TestEloUpdates(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        # Create two users with initial ELOs
        self.user1 = Usuario.objects.create(
            nombre="user1", 
            correo="user1@example.com", 
            contrasegna="password", 
            elo=1200
        )
        self.user1.save()
        self.user2 = Usuario.objects.create(
            nombre="user2", 
            correo="user2@example.com", 
            contrasegna="password", 
            elo=1200
        )
        self.user2.save()
        # Generate JWT tokens
        self.token1 = generar_token(self.user1)
        self.token2 = generar_token(self.user2)
        
        # Create a mock partida
        self.partida = Partida.objects.create(capacidad=2, estado='jugando')
        self.partida.save()
        self.jugador1 = JugadorPartida.objects.create(partida=self.partida, usuario=self.user1, equipo=1)
        self.jugador2 = JugadorPartida.objects.create(partida=self.partida, usuario=self.user2, equipo=2)


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

            # Check that ELOs have been updated
            self.assertNotEqual(self.user1.elo, 1200)  # Should have increased
            self.assertNotEqual(self.user2.elo, 1200)  # Should have decreased
            self.assertGreater(self.user1.elo, self.user2.elo)  # Winner should have higher ELO

        async_to_sync(inner)()
