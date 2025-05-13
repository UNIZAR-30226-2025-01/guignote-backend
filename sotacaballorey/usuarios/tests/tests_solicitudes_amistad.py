from django.contrib.auth.hashers import make_password
from usuarios.models import Usuario, SolicitudAmistad
from utils.jwt_auth import generar_token
from django.test import TestCase, Client
import json
from django.core.management import call_command

class SolicitudAmistadTests(TestCase):
    fixtures = [
            'aspecto_carta/fixtures/initial_data.json',
            'tapete/fixtures/initial_data.json'
        ]
    for fixture in fixtures:
            call_command('loaddata', fixture)
            
    def setUp(self):
        super().setUp()
        self.cliente = Client()

        # Usuario principal que usaremos en las pruebas
        self.usuario = Usuario.objects.create(
            nombre='usuario',
            correo='usuario@gmail.com',
            contrasegna=make_password("123456")
        )
        self.usuario.save()
        self.token = generar_token(self.usuario)

    def test_enviar_solicitud_amistad(self):
        """
        Prueba para enviar solicitud de amistad
        """

        # Creo usuario al que enviaré solicitud de amistad
        amigo = Usuario.objects.create(
            nombre="amigo",
            correo="amigo@gmail.com",
            contrasegna=make_password("654321")
        )
        
        # El primero le envía una solicitud de amistad al segundo
        respuesta = self.cliente.post('/usuarios/enviar_solicitud_amistad/', json.dumps({
            'destinatario_id': amigo.id
        }), content_type='application/json', HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 201)
        self.assertTrue(SolicitudAmistad.objects.filter(emisor=self.usuario, receptor=amigo).exists())

        # Error por falta de campos
        respuesta = self.cliente.post('/usuarios/enviar_solicitud_amistad/',
             content_type='application/json', HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 400)


        # Error destinatario no encontrado
        respuesta = self.cliente.post('/usuarios/enviar_solicitud_amistad/', json.dumps({
            'destinatario_id': -1
        }), content_type='application/json', HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 404)

        # Error la solicitud ya fue enviada
        respuesta = self.cliente.post('/usuarios/enviar_solicitud_amistad/', json.dumps({
            'destinatario_id': amigo.id
        }), content_type='application/json', HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 400)

    def test_aceptar_solicitud_amistad(self):
        """
        Prueba aceptación de una solicitud de amistad
        """
        
        # Creo amigo y solicitud de amistad
        amigo = Usuario.objects.create(
            nombre="amigo",
            correo="amigo@gmail.com",
            contrasegna=make_password("654321")
        )
        solicitud = SolicitudAmistad.objects.create(emisor=amigo, receptor=self.usuario)

        # Acepto la solicitud de amistad de amigo
        respuesta = self.client.post('/usuarios/aceptar_solicitud_amistad/', json.dumps({
            'solicitud_id': solicitud.id
        }), content_type="application/json", HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(SolicitudAmistad.objects.filter(id=solicitud.id).exists())
        self.assertTrue(self.usuario.amigos.filter(id=amigo.id).exists())

        # Error por falta de campos
        respuesta = self.client.post('/usuarios/aceptar_solicitud_amistad/', json.dumps({}), content_type="application/json", HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 400)

        # Error no existe la solicitud de amistad
        respuesta = self.client.post('/usuarios/aceptar_solicitud_amistad/', json.dumps({
            'solicitud_id': -1
        }), content_type="application/json", HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 404)

        # Error no puedes aceptar una solicitud para la que no eres destinatario
        solicitud = SolicitudAmistad.objects.create(emisor=self.usuario, receptor=amigo)
        respuesta = self.client.post('/usuarios/aceptar_solicitud_amistad/', json.dumps({
            'solicitud_id': solicitud.id
        }), content_type="application/json", HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 403)

    def test_denegar_solicitud_amistad(self):
        """
        Prueba denegar solicitud amistad
        """
        # Creo un usuario y solicitud de amistad
        amigo = Usuario.objects.create(
            nombre="amigo",
            correo="amigo@gmail.com",
            contrasegna=make_password("654321")
        )
        solicitud = SolicitudAmistad.objects.create(emisor=amigo, receptor=self.usuario)

        # Rechazo la solicitud de amistad del usuario
        respuesta = self.client.post('/usuarios/denegar_solicitud_amistad/', json.dumps({
            'solicitud_id': solicitud.id
        }), content_type="application/json", HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(SolicitudAmistad.objects.filter(id=solicitud.id).exists())
        self.assertFalse(self.usuario.amigos.filter(id=amigo.id).exists())

        # Error por falta de campos
        respuesta = self.client.post('/usuarios/denegar_solicitud_amistad/', json.dumps({}), content_type="application/json", HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 400)

        # Error no existe la solicitud de amistad
        respuesta = self.client.post('/usuarios/denegar_solicitud_amistad/', json.dumps({
            'solicitud_id': -1
        }), content_type="application/json", HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 404)

        # Error no puedes denegar una solicitud para la que no eres destinatario
        solicitud = SolicitudAmistad.objects.create(emisor=self.usuario, receptor=amigo)
        respuesta = self.client.post('/usuarios/denegar_solicitud_amistad/', json.dumps({
            'solicitud_id': solicitud.id
        }), content_type="application/json", HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 403)

    def test_listar_solicitudes_amistad(self):
        """
        Prueba listado solicitudes de amistad
        """

        # Creo amigo y una solicitud de amistad
        amigo = Usuario.objects.create(
            nombre="amigo",
            correo="amigo@gmail.com",
            contrasegna=make_password("654321")
        )
        solicitud = SolicitudAmistad.objects.create(emisor=amigo, receptor=self.usuario)

        # Compruebo que en el listado tengo una solicitud de amistad y que además una
        # de las solicitudes tiene como id, el id de la solicitud anterior
        respuesta = self.client.get('/usuarios/listar_solicitudes_amistad/', HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 200)
        solicitudes_json = respuesta.json().get('solicitudes', [])
        self.assertGreater(len(solicitudes_json), 0)
        solicitud_ids = [s['id'] for s in solicitudes_json]
        self.assertIn(solicitud.id, solicitud_ids)

    def test_eliminar_amigo(self):
        """
        Prueba para la eliminación de un amigo de la lista de amigos
        """

        # Creo amigo y lo añado a la lista de amigos
        amigo = Usuario.objects.create(
            nombre="amigo",
            correo="amigo@gmail.com",
            contrasegna=make_password("654321")
        )
        self.usuario.amigos.add(amigo)

        # Eliminar amigo
        respuesta = self.client.delete(f'/usuarios/eliminar_amigo/?amigo_id={amigo.id}', HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 200)
        self.usuario.refresh_from_db()
        self.assertNotIn(amigo, self.usuario.amigos.all())

        # Error faltan campos
        respuesta = self.client.delete('/usuarios/eliminar_amigo/', HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 400)

        # Error amigo no encontrado
        respuesta = self.client.delete(f'/usuarios/eliminar_amigo/?amigo_id={-1}', HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 404)

    def test_obtener_amigos(self):
        """
        Prueba para obtener lista de amigos
        """
        
        # Creo dos amigos y los añado a lista de amigos
        amigo1 = Usuario.objects.create(nombre="amigo1", correo="amigo1@example.com", contrasegna="password123")
        amigo2 = Usuario.objects.create(nombre="amigo2", correo="amigo2@example.com", contrasegna="password456")
        self.usuario.amigos.add(amigo1, amigo2)

        # Obtener lista de amigos
        respuesta = self.client.get('/usuarios/obtener_amigos/', HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 200)
        amigos_json = respuesta.json().get('amigos', [])
        amigos_ids = [a['id'] for a in amigos_json]

        # Comprobamos que los amigos creados anteriormente salen en la lista
        self.assertIn(amigo1.id, amigos_ids)
        self.assertIn(amigo2.id, amigos_ids)

    def test_buscar_usuarios(self):
        
        # Creo varios usuarios
        usuario1 = Usuario.objects.create(nombre="Juan", correo="juan@example.com", contrasegna="password123")
        usuario2 = Usuario.objects.create(nombre="Juana", correo="juana@example.com", contrasegna="password456")
        usuario3 = Usuario.objects.create(nombre="Carlos", correo="carlos@example.com", contrasegna="password789")

        # Hago la petición y busco usuarios cuyo nombre contiente "Jua"
        respuesta = self.client.get('/usuarios/buscar_usuarios/?nombre=Juan', HTTP_AUTH=self.token)
        self.assertEqual(respuesta.status_code, 200)

        # Verifico que "Juan" y "Juana" aparecen en la lista, pero no "Carlos"
        usuarios_json = respuesta.json().get('usuarios', [])
        usuarios_nombres = [u['nombre'] for u in usuarios_json]
        self.assertIn("Juan", usuarios_nombres)
        self.assertIn("Juana", usuarios_nombres)
        self.assertNotIn("Carlos", usuarios_nombres)
