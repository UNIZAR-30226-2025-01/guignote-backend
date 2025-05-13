from django.test import TestCase, TransactionTestCase, Client
from utils.jwt_auth import generar_token
from chat_global.models import Chat, Mensaje
from usuarios.models import Usuario
import json
from django.core.management import call_command

class ChatGlobalTest(TestCase):

    fixtures = [
            'aspecto_carta/fixtures/initial_data.json',
            'tapete/fixtures/initial_data.json'
        ]
    for fixture in fixtures:
            call_command('loaddata', fixture)

    def setUp(self):
        self.cliente = Client()

        # Creo usuarios de prueba
        self.usuario1 = Usuario.objects.create(
            nombre = "Jorge", correo = "jorge@gmail.com", contrasegna='123'
        )
        self.usuario2 = Usuario.objects.create(
            nombre = "Diego", correo = "diego@gmail.com", contrasegna='123'
        )

        # Los hago amigos
        self.usuario1.amigos.add(self.usuario2)
        self.usuario2.amigos.add(self.usuario1)

        # Crear un chat entre los dos
        self.chat = Chat.objects.create(
            usuario1=self.usuario1,
            usuario2=self.usuario2
        )

        # Obtener tokens
        self.token_usuario1 = generar_token(self.usuario1)
        self.token_usuario2 = generar_token(self.usuario2)
    
    def test_enviar_mensaje(self):
        """
        Probar enviar mensaje con petición POST
        """
        respuesta = self.client.post(
            '/mensajes/enviar/',
            json.dumps({
                'receptor_id': self.usuario2.id,
                'contenido': '¡Hola, mundo!'
            }), content_type='application/json',
            HTTP_AUTH=self.token_usuario1
        )
        self.assertEqual(respuesta.status_code, 201)
        mensaje = Mensaje.objects.filter(
            chat=self.chat, emisor=self.usuario1, contenido='¡Hola, mundo!').exists()
        self.assertGreater(self.chat.mensajes_glob.all().count(), 0)
        self.assertTrue(mensaje)

        # Error por falta de campos
        respuesta = self.client.post(
            '/mensajes/enviar/',
            json.dumps({
                'receptor_id': self.usuario2.id
            }), content_type='application/json',
            HTTP_AUTH=self.token_usuario1
        )
        self.assertEqual(respuesta.status_code, 400)

        # Error por receptor inexistente
        respuesta = self.client.post(
            '/mensajes/enviar/',
            json.dumps({
                'receptor_id': -1,
                'contenido': '¡Hola, mundo!'
            }), content_type='application/json',
            HTTP_AUTH=self.token_usuario1
        )
        self.assertEqual(respuesta.status_code, 404)

        # Error por enviar un mensaje a alguién que no es tu amigo
        noAmigo = Usuario.objects.create(
            nombre='Alejandro', correo='alejandro@gmail', contrasegna='123'
        )
        respuesta = self.client.post(
            '/mensajes/enviar/',
            json.dumps({
                'receptor_id': noAmigo.id,
                'contenido': '¡Hola, mundo!'
            }), content_type='application/json',
            HTTP_AUTH=self.token_usuario1
        )
        self.assertEqual(respuesta.status_code, 403)

    def test_obtener_mensajes(self):
        # Crear mensaje en el chat
        Mensaje.objects.create(
            chat=self.chat, emisor=self.usuario1, contenido='¡Hola, unizar!'
        )

        respuesta = self.client.get(
            f'/mensajes/obtener/?receptor_id={self.usuario2.id}',
            HTTP_AUTH=self.token_usuario1
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            respuesta.json()['mensajes'][0]['contenido'],
            '¡Hola, unizar!'
        )

        # Error por receptor inexistente
        respuesta = self.cliente.get(
            '/mensajes/obtener/?receptor_id=-1',
            HTTP_AUTH=self.token_usuario1
        )
        self.assertEqual(respuesta.status_code, 404)

        # Error por falta de token
        respuesta = self.cliente.get(
            f'/mensajes/obtener/?receptor_id={self.usuario2.id}'
        )
        self.assertEqual(respuesta.status_code, 401)