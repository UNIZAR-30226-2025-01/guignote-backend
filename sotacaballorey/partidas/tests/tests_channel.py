
from channels.testing import WebsocketCommunicator
from partidas.consumers import PartidaConsumer
from django.test import TransactionTestCase
from sotacaballorey.asgi import application
from utils.jwt_auth import generar_token
from asgiref.sync import async_to_sync
from usuarios.models import Usuario
import json

class PartidaConsumerTest(TransactionTestCase):
    
    reset_sequences = True

    def setUp(self):
        PartidaConsumer.TIEMPO_TURNO = 5
        self.user1 = Usuario.objects.create(
            nombre='Usuario 1', correo='user1@gmail.com', contrasegna='123')
        self.user2 = Usuario.objects.create(
            nombre='Usuario 2', correo='user2@gmail.com', contrasegna='123')
        self.token1 = generar_token(self.user1)
        self.token2 = generar_token(self.user2)

    def test_partida_dos_usuarios(self):
        
        async def inner():

            # Se conecta el usuario 1
            url1 = f'/ws/partida/?token={self.token1}&capacidad=2'
            comm1 = WebsocketCommunicator(application, url1)
            connected1, _ = await comm1.connect()
            self.assertTrue(connected1)

            # El usuario 1 recibe mensaje "player_joined" con su info
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'player_joined')
            self.assertTrue(data['data']['usuario']['id'], self.user1.id)

            # Se conecta el usuario 2
            url2 = f'/ws/partida/?token={self.token2}&id_partida=1'
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

            self.assertTrue(self.turno, turno)

            # El jugador que tiene el turno hace una jugada
            if self.turno == self.user1.id:
                comm_turno = comm1
                carta = self.mano_1[0]
                carta_2 = self.mano_2[0]
            else:
                comm_turno = comm2
                carta = self.mano_2[0]
                carta_2 = self.mano_1[0]

            # El jugador hace jugada errónea (carta no existe)
            jugada = {'accion': 'jugar_carta', 'carta': {'palo': 'caca', 'valor': 1}}
            await comm_turno.send_to(text_data=json.dumps(jugada))
            response = await comm_turno.receive_from(timeout=5)
            data = json.loads(response)
            self.assertTrue(data['type'], 'error')

            # El jugador hace jugada errónea (carta no está en su mano)
            jugada = {'accion': 'jugar_carta', 'carta':carta_2}
            await comm_turno.send_to(text_data=json.dumps(jugada))
            response = await comm_turno.receive_from(timeout=5)
            data = json.loads(response)
            self.assertTrue(data['type'], 'error')

            # El jugador hace jugada correcta
            jugada = {'accion': 'jugar_carta', 'carta':carta}
            await comm_turno.send_to(text_data=json.dumps(jugada))

            # Ambos jugadores recibirán mensaje con la jugada que ha hecho
            # el jugador que tenía el turno
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'card_played')
            self.assertTrue(data['data']['jugador']['id'], self.turno)
            self.assertEqual(data['data']['automatica'], False)
            self.assertIn(data['data']['carta'], self.mano_1)

            msg = await comm2.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'card_played')
            self.assertTrue(data['data']['jugador']['id'], self.turno)
            self.assertEqual(data['data']['automatica'], False)
            self.assertIn(data['data']['carta'], self.mano_1)

            # Ambos reciben mensaje de nuevo turno
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'turn_update')
            self.turno = data['data']['jugador']['id']

            msg = await comm2.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'turn_update')
            turno = data['data']['jugador']['id']

            self.assertTrue(self.turno, turno)

            # El jugador con el nuevo turno no tirará ninguna carta. A los
            # 20 seg el tiempo de turno expirará y el servidor tirará una
            # carta aleatoria válida por él automáticamente
            msg = await comm1.receive_from(timeout=25)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'card_played')
            self.assertEqual(data['data']['automatica'], True)
            self.assertIn(data['data']['carta'], self.mano_2)

            msg = await comm2.receive_from(timeout=25)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'card_played')
            self.assertEqual(data['data']['automatica'], True)
            self.assertIn(data['data']['carta'], self.mano_2)

            # Ambos jugadores han tirado carta en la baza. Comprobamos que reciben
            # mensaje con el ganador de la baza
            msg = await comm1.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'round_result')

            msg = await comm2.receive_from(timeout=5)
            data = json.loads(msg)
            self.assertTrue(data['type'], 'round_result')


            # Ambos jugadores roban una carta y reciben qué carta han robado
            msg = await comm1.receive_from(timeout=5)
            data_1 = json.loads(msg)
            self.assertTrue(data['type'], 'card_drawn')

            msg = await comm2.receive_from(timeout=5)
            data_2 = json.loads(msg)
            self.assertTrue(data['type'], 'card_drawn')

            self.assertNotEqual(data_1['data']['carta'], data_2['data']['carta'])

            await comm1.disconnect()
            await comm2.disconnect()

        async_to_sync(inner)()