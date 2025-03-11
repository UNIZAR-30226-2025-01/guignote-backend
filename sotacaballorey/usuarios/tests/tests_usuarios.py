from django.test import TestCase, Client
from usuarios.models import Usuario
from django.urls import reverse
import json

class UsuarioTests(TestCase):

    def setUp(self):
        super().setUp()
        self.cliente = Client()
        self.usuario1 = Usuario.objects.create(nombre="Carlos", correo="carlos@example.com", contrasegna="1234")
        self.usuario2 = Usuario.objects.create(nombre="Elena", correo="elena@example.com", contrasegna="1234")

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
        
    def test_obtener_id_por_nombre_existente(self):
            """Test retrieving user ID for an existing username."""
            response = self.client.get(reverse('obtener_id_por_nombre', args=[self.usuario1.nombre]))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["user_id"], self.usuario1.id)

    def test_obtener_id_por_nombre_no_existente(self):
        """Test retrieving user ID for a username that does not exist."""
        response = self.client.get(reverse('obtener_id_por_nombre', args=["UsuarioInexistente"]))
        self.assertEqual(response.status_code, 404)  # Should return "Not Found"