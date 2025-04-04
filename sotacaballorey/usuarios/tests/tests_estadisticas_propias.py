from django.test import TestCase
from django.urls import reverse
from usuarios.models import Usuario
from partidas.models import Partida
from utils.jwt_auth import generar_token  # Import JWT authentication utility
import json


class EstadisticasUsuarioTestCase(TestCase):

    def setUp(self):
        """Setup users, matches, and generate authentication tokens."""
        self.usuario1 = Usuario.objects.create(
            nombre="Carlos", correo="carlos@example.com", contrasegna="1234",
            victorias=5, derrotas=2, racha_victorias=3, mayor_racha_victorias=4
        )

        self.usuario2 = Usuario.objects.create(
            nombre="Elena", correo="elena@example.com", contrasegna="1234",
            victorias=10, derrotas=5, racha_victorias=2, mayor_racha_victorias=5
        )

        # Generate JWT tokens
        self.token_usuario1 = generar_token(self.usuario1)
        self.token_usuario2 = generar_token(self.usuario2)

    def test_obtener_total_partidas(self):
        """Test retrieving total games played by the authenticated user."""
        response = self.client.get(
            reverse('obtener_total_partidas'),
            HTTP_AUTH=self.token_usuario1
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_partidas"], self.usuario1.victorias + self.usuario1.derrotas)

    def test_obtener_porcentaje_victorias(self):
        """Test retrieving win percentage for the authenticated user."""
        response = self.client.get(
            reverse('obtener_porcentaje_victorias'),
            HTTP_AUTH=self.token_usuario1
        )
        self.assertEqual(response.status_code, 200)

        expected_win_percentage = round((self.usuario1.victorias / (self.usuario1.victorias + self.usuario1.derrotas)) * 100, 2)
        self.assertEqual(response.json()["porcentaje_victorias"], expected_win_percentage)

    def test_obtener_porcentaje_derrotas(self):
        """Test retrieving loss percentage for the authenticated user."""
        response = self.client.get(
            reverse('obtener_porcentaje_derrotas'),
            HTTP_AUTH=self.token_usuario1
        )
        self.assertEqual(response.status_code, 200)

        expected_loss_percentage = round((self.usuario1.derrotas / (self.usuario1.victorias + self.usuario1.derrotas)) * 100, 2)
        self.assertEqual(response.json()["porcentaje_derrotas"], expected_loss_percentage)

    def test_obtener_racha_actual(self):
        """Test retrieving the current winning streak for the authenticated user."""
        response = self.client.get(
            reverse('obtener_racha_actual'),
            HTTP_AUTH=self.token_usuario1
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["racha_victorias"], self.usuario1.racha_victorias)

    def test_obtener_racha_mas_larga(self):
        """Test retrieving the longest winning streak for the authenticated user."""
        response = self.client.get(
            reverse('obtener_racha_mas_larga'),
            HTTP_AUTH=self.token_usuario1
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mayor_racha_victorias"], self.usuario1.mayor_racha_victorias)

    def test_obtener_usuario_estadisticas(self):
        """Test retrieving all statistics for the authenticated user."""
        response = self.client.get(
            reverse('obtener_usuario_estadisticas'),
            HTTP_AUTH=self.token_usuario1
        )
        self.assertEqual(response.status_code, 200)

        expected_data = {
            "nombre": self.usuario1.nombre,
            "victorias": self.usuario1.victorias,
            "derrotas": self.usuario1.derrotas,
            "racha_victorias": self.usuario1.racha_victorias,
            "mayor_racha_victorias": self.usuario1.mayor_racha_victorias,
            "total_partidas": self.usuario1.victorias + self.usuario1.derrotas,
            "porcentaje_victorias": round((self.usuario1.victorias / (self.usuario1.victorias + self.usuario1.derrotas)) * 100, 2),
            "imagen": 'http://testserver/media/imagenes_perfil/default.webp',
            "porcentaje_derrotas": round((self.usuario1.derrotas / (self.usuario1.victorias + self.usuario1.derrotas)) * 100, 2),
            "elo_parejas": 1200,
            "elo": 1200
        }

        self.assertEqual(response.json(), expected_data)

    def test_sin_token_devuelve_401(self):
        """Test that accessing statistics without a token returns a 401 Unauthorized."""
        response = self.client.get(reverse('obtener_total_partidas'))
        self.assertEqual(response.status_code, 401)

    def test_otro_usuario_no_puede_acceder_a_mi_estadistica(self):
        """Test that a user cannot access another user's statistics."""
        response = self.client.get(
            reverse('obtener_usuario_estadisticas'),
            HTTP_AUTH=self.token_usuario2
        )
        self.assertEqual(response.status_code, 200)

        # Should return usuario2's statistics, not usuario1's
        self.assertNotEqual(response.json()["nombre"], self.usuario1.nombre)
        self.assertEqual(response.json()["nombre"], self.usuario2.nombre)
