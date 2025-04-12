from partidas.models import Partida, JugadorPartida
from django.test import TestCase, Client
from utils.jwt_auth import generar_token
from usuarios.models import Usuario

class SalaTests(TestCase):
   
    def setUp(self):
        self.cliente = Client()

        # Crear usuario para las pruebas y generar su token
        self.usuario = Usuario.objects.create(
            nombre='Usuario', correo='usuario@gmail.com', contrasegna='123'
        )
        self.token = generar_token(self.usuario)

    def test_listar_salas_disponibles(self):
        """
        Test de petición que lista salas disponibles, es decir, salas
        no llenas que están en estado 'esperando'. Se puede especificar
        la capacidad de las salas
        """
        # Creamos partidas con distintos estados y capacidades
        p1 = Partida.objects.create(capacidad=2, estado='esperando')
        p2 = Partida.objects.create(capacidad=2, estado='esperando')
        p3 = Partida.objects.create(capacidad=2, estado='jugando')

        p4 = Partida.objects.create(capacidad=4, estado='esperando')
        p5 = Partida.objects.create(capacidad=4, estado='esperando')
        p6 = Partida.objects.create(capacidad=4, estado='jugando')

        # Hacemos petición sin filtrar capacidad
        respuesta = self.cliente.get('/salas/disponibles/', HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 200)
        salas = respuesta.json().get('salas', [])
        ids = [s['id'] for s in salas]
        self.assertIn(p1.id, ids)
        self.assertIn(p2.id, ids)
        self.assertIn(p4.id, ids)
        self.assertIn(p5.id, ids)
        self.assertEqual(len(salas), 4)

        # Filtamos capacidad=2
        respuesta = self.cliente.get('/salas/disponibles/?capacidad=2', HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 200)
        salas = respuesta.json().get('salas', [])
        for s in salas:
            self.assertEqual(s['capacidad'], 2)
        self.assertEqual(len(salas), 2)

        # Filtramos capacidad=4
        respuesta = self.cliente.get('/salas/disponibles/?capacidad=4', HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 200)
        salas = respuesta.json().get('salas', [])
        for s in salas:
            self.assertEqual(s['capacidad'], 4)
        self.assertEqual(len(salas), 2)

    def test_listar_salas_reconectables(self):
        """
        Test de petición que lista las salas/partidas no terminadas en las que
        jugaste y te desconectaste, es decir, aquellas salas llenas con estado 'jugando'
        y en las que eres uno de los jugadores
        """
        # Creamos una partida activa en la que el usuario está desconectado
        p1 = Partida.objects.create(capacidad=2, estado='jugando')
        JugadorPartida.objects.create(partida=p1, usuario=self.usuario, conectado=False)

        # Partida esperando (no debe aparecer)
        p2 = Partida.objects.create(capacidad=2, estado='esperando')
        JugadorPartida.objects.create(partida=p2, usuario=self.usuario, conectado=False)

        # Partida jugando pero conectado (no debe aparecer)
        p3 = Partida.objects.create(capacidad=2, estado='jugando')
        JugadorPartida.objects.create(partida=p3, usuario=self.usuario, conectado=True)

        # Hacemos la petición
        respuesta = self.cliente.get('/salas/reconectables/', HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 200)
        salas = respuesta.json().get('salas', [])
        ids = [s['id'] for s in salas]
        self.assertIn(p1.id, ids)
        self.assertNotIn(p2.id, ids)
        self.assertNotIn(p3.id, ids)