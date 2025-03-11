from django.test import TestCase
from django.urls import reverse
from usuarios.models import Usuario
from partidas.models import Partida
from utils.jwt_auth import generar_token
from partidas.elo import calcular_nuevo_elo
import json


class EloTestCase(TestCase):

    def setUp(self):
        """Setup before each test - Create users, matches, and generate tokens."""
        self.jugador1 = Usuario.objects.create(nombre="Carlos", correo="carlos@example.com", contrasegna="1234", elo=1200)
        self.jugador2 = Usuario.objects.create(nombre="Elena", correo="elena@example.com", contrasegna="1234", elo=1200)

        # Generate authentication tokens
        self.token_jugador1 = generar_token(self.jugador1)
        self.token_jugador2 = generar_token(self.jugador2)

    def test_elo_calculation(self):
        """Test that Elo calculation works correctly after multiple matches."""

        partidas = []

        # 🔹 First 3 matches: jugador1 wins
        for _ in range(3):
            partida = Partida.objects.create(jugador_1=self.jugador1, jugador_2=self.jugador2, estado_partida="EN_JUEGO")
            partidas.append(partida)

            request_data = {"estado": "FINALIZADO", "ganador_id": self.jugador1.id}
            response = self.client.post(
                reverse('cambiar_estado_partida', args=[partida.id]),
                data=json.dumps(request_data),
                content_type="application/json",
                HTTP_AUTH=self.token_jugador1
            )
            self.assertEqual(response.status_code, 200)

            # Refresh ratings
            self.jugador1.refresh_from_db()
            self.jugador2.refresh_from_db()

        # Elo should have increased for jugador1 and decreased for jugador2
        self.assertGreater(self.jugador1.elo, 1200)
        self.assertLess(self.jugador2.elo, 1200)

        # 🔹 1 match where jugador2 wins
        partida = Partida.objects.create(jugador_1=self.jugador1, jugador_2=self.jugador2, estado_partida="EN_JUEGO")
        partidas.append(partida)

        request_data = {"estado": "FINALIZADO", "ganador_id": self.jugador2.id}
        response = self.client.post(
            reverse('cambiar_estado_partida', args=[partida.id]),
            data=json.dumps(request_data),
            content_type="application/json",
            HTTP_AUTH=self.token_jugador2
        )
        self.assertEqual(response.status_code, 200)

        # Refresh ratings again
        self.jugador1.refresh_from_db()
        self.jugador2.refresh_from_db()

        # Elo should have adjusted in the opposite direction now
        self.assertLess(self.jugador1.elo, self.jugador1.elo + 32)  # Lost points
        self.assertGreater(self.jugador2.elo, self.jugador2.elo - 32)  # Gained points

    def test_retrieve_elo(self):
        """Test that Elo retrieval functions return the same value across all endpoints."""

        # Retrieve via token-based function
        response_token = self.client.get(
            reverse('obtener_elo'),
            HTTP_AUTH=self.token_jugador1
        )
        self.assertEqual(response_token.status_code, 200)
        elo_token = response_token.json().get("elo")
        self.assertIsNotNone(elo_token)

        # Retrieve via direct user-based function
        response_direct = self.client.get(
            reverse('obtener_elo', args=[self.jugador1.id]),
            HTTP_AUTH=self.token_jugador1
        )
        self.assertEqual(response_direct.status_code, 200)
        elo_direct = response_direct.json().get("elo")
        self.assertIsNotNone(elo_direct)

        # Retrieve via general stats function
        response_stats = self.client.get(
            reverse('obtener_usuario_estadisticas', args=[self.jugador1.id]),
            HTTP_AUTH=self.token_jugador1
        )
        self.assertEqual(response_stats.status_code, 200)
        elo_stats = response_stats.json().get("elo")
        self.assertIsNotNone(elo_stats)
        
        response_stats_direct = self.client.get(
            reverse('obtener_usuario_estadisticas'),
            HTTP_AUTH=self.token_jugador1
        )
        self.assertEqual(response_stats_direct.status_code, 200)
        elo_stats_direct = response_stats.json().get("elo")
        self.assertIsNotNone(elo_stats_direct)

        # 🔹 Ensure all retrieved Elo values are the same
        self.assertEqual(elo_token, elo_direct)
        self.assertEqual(elo_direct, elo_stats)
        self.assertEqual(elo_stats, elo_stats_direct)
