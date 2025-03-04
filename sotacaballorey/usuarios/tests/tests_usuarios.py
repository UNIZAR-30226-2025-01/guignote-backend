from django.test import TestCase, Client
import json

class UsuarioTests(TestCase):

    def setUp(self):
        super().setUp()
        self.cliente = Client()

    def test_crear_usuario(self):
        """
        Probar la creación de un usuario
        """
        
        # Crear usuario nuevo
        respuesta = self.cliente.post('/usuarios/crear_usuario/', json.dumps({
            'nombre': 'nom',
            'correo': 'nom@gmail.com',
            'contrasegna': '123456'
        }), content_type='application/json')
        self.assertEqual(respuesta.status_code, 201)
        self.assertIn('token', respuesta.json())

        # Error por nombre ya usado
        respuesta = self.cliente.post('/usuarios/crear_usuario/', json.dumps({
            'nombre': 'nom',
            'correo': 'nuevoNom@gmail.com',
            'contrasegna': '123456'
        }), content_type='application/json')
        self.assertEqual(respuesta.status_code, 400)

        # Error por correo ya usado
        respuesta = self.cliente.post('/usuarios/crear_usuario/', json.dumps({
            'nombre': 'nuevoNom',
            'correo': 'nom@gmail.com',
            'contrasegna': '123456'
        }), content_type='application/json')
        self.assertEqual(respuesta.status_code, 400)

        # Error campos insuficientes
        respuesta = self.cliente.post('/usuarios/crear_usuario/', json.dumps({
            'nombre': 'nuevoNom',
            'contrasegna': '123456'
        }), content_type='application/json')
        self.assertEqual(respuesta.status_code, 400)

    def test_iniciar_sesion(self):
        """
        Prueba inicio sesión
        """

        # Creo un usuario
        respuesta = self.cliente.post('/usuarios/crear_usuario/', json.dumps({
            'nombre': 'nom',
            'correo': 'nom@gmail.com',
            'contrasegna': '123456'
        }), content_type='application/json')
        self.assertEqual(respuesta.status_code, 201)
        self.assertIn('token', respuesta.json())

        # Inicio sesión con su nombre y contraseña
        respuesta = self.cliente.post('/usuarios/iniciar_sesion/', json.dumps({
            'nombre': 'nom',
            'contrasegna': '123456'
        }), content_type='application/json')
        self.assertEqual(respuesta.status_code, 201)
        self.assertIn('token', respuesta.json())

        # Inicio sesión con su correo y contraseña
        respuesta = self.cliente.post('/usuarios/iniciar_sesion/', json.dumps({
            'correo': 'nom@gmail.com',
            'contrasegna': '123456'
        }), content_type='application/json')
        self.assertEqual(respuesta.status_code, 201)
        self.assertIn('token', respuesta.json())

        # Error por contraseña incorrecta
        respuesta = self.cliente.post('/usuarios/iniciar_sesion/', json.dumps({
            'correo': 'nom@gmail.com',
            'contrasegna': '654321'
        }), content_type='application/json')
        self.assertEqual(respuesta.status_code, 400)

        # Error por usuario no encontrado
        respuesta = self.cliente.post('/usuarios/iniciar_sesion/', json.dumps({
            'correo': 'noExisto@gmail.com',
            'contrasegna': '123456'
        }), content_type='application/json')
        self.assertEqual(respuesta.status_code, 404)

        # Error campos insuficientes
        respuesta = self.cliente.post('/usuarios/iniciar_sesion/', json.dumps({
            'contrasegna': '123456'
        }), content_type='application/json')
        self.assertEqual(respuesta.status_code, 400)

    def test_eliminar_usuario(self):
        """
        Prueba para la eliminación de un usuario
        """

        # Creo un usuario
        respuesta = self.cliente.post('/usuarios/crear_usuario/', json.dumps({
            'nombre': 'nom',
            'correo': 'nom@gmail.com',
            'contrasegna': '123456'
        }), content_type='application/json')
        self.assertEqual(respuesta.status_code, 201)
        self.assertIn('token', respuesta.json())
        token = respuesta.json().get('token')

        # Lo elimino
        respuesta = self.cliente.delete('/usuarios/eliminar_usuario/', HTTP_AUTH=token)
        self.assertEqual(respuesta.status_code, 200)

        # Error por token no válido o expirado
        respuesta = self.cliente.delete('/usuarios/eliminar_usuario/', HTTP_AUTH='123')
        self.assertEqual(respuesta.status_code, 401)

        # Error por token no proporcionado
        respuesta = self.cliente.delete('/usuarios/eliminar_usuario/')
        self.assertEqual(respuesta.status_code, 401)