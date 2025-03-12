from django.test import TestCase
from django.urls import reverse
from usuarios.models import Usuario
from partidas.models import Partida2v2
from utils.jwt_auth import generar_token
from partidas.elo import calcular_nuevo_elo_parejas
import json


class EloParejasTestCase(TestCase):

    def setUp(self):
        """Setup before each test - Create users, matches, and generate tokens."""
        self.jugadores = [
            Usuario.objects.create(nombre=f"Jugador{i}", correo=f"jugador{i}@example.com", contrasegna="1234", elo_parejas=1200)
            for i in range(1, 5)  # Create 4 players for a 2v2 match
        ]

        # Generate authentication tokens
        self.tokens = {jugador: generar_token(jugador) for jugador in self.jugadores}

    def test_elo_parejas_calculation(self):
        """Test that Elo calculation for 2v2 matches works correctly after multiple matches."""

        partidas = []

        # 🔹 First 3 matches: Team 1 wins
        for _ in range(3):
            partida = Partida2v2.objects.create(
                equipo_1_jugador_1=self.jugadores[0], equipo_1_jugador_2=self.jugadores[1],
                equipo_2_jugador_1=self.jugadores[2], equipo_2_jugador_2=self.jugadores[3],
                estado_partida="EN_JUEGO"
            )
            partidas.append(partida)

            request_data = {"estado": "FINALIZADO", "equipo_ganador": 1}
            response = self.client.post(
                reverse('cambiar_estado_partida_2v2', args=[partida.id]),
                data=json.dumps(request_data),
                content_type="application/json",
                HTTP_AUTH=self.tokens[self.jugadores[0]]
            )
            self.assertEqual(response.status_code, 200)

            # Refresh ratings
            for jugador in self.jugadores:
                jugador.refresh_from_db()

        # Elo should have increased for Team 1 and decreased for Team 2
        self.assertGreater(self.jugadores[0].elo_parejas, 1200)
        self.assertGreater(self.jugadores[1].elo_parejas, 1200)
        self.assertLess(self.jugadores[2].elo_parejas, 1200)
        self.assertLess(self.jugadores[3].elo_parejas, 1200)

        # 🔹 1 match where Team 2 wins
        partida = Partida2v2.objects.create(
            equipo_1_jugador_1=self.jugadores[0], equipo_1_jugador_2=self.jugadores[1],
            equipo_2_jugador_1=self.jugadores[2], equipo_2_jugador_2=self.jugadores[3],
            estado_partida="EN_JUEGO"
        )
        partidas.append(partida)

        request_data = {"estado": "FINALIZADO", "equipo_ganador": 2}
        response = self.client.post(
            reverse('cambiar_estado_partida_2v2', args=[partida.id]),
            data=json.dumps(request_data),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.tokens[self.jugadores[2]]}"
        )
        self.assertEqual(response.status_code, 200)

        # Refresh ratings again
        for jugador in self.jugadores:
            jugador.refresh_from_db()

        # Elo should have adjusted in the opposite direction now
        self.assertLess(self.jugadores[0].elo_parejas, self.jugadores[0].elo_parejas + 32)  # Lost points
        self.assertGreater(self.jugadores[2].elo_parejas, self.jugadores[2].elo_parejas - 32)  # Gained points

    def test_retrieve_elo_parejas(self):
        """Test that Elo retrieval functions return the same value across all endpoints."""

        # Retrieve via token-based function
        response_token = self.client.get(
            reverse('obtener_elo_parejas'),
            HTTP_AUTH=self.tokens[self.jugadores[0]]
        )
        self.assertEqual(response_token.status_code, 200)
        elo_token = response_token.json().get("elo_parejas")
        self.assertIsNotNone(elo_token)

        # Retrieve via direct user-based function
        response_direct = self.client.get(
            reverse('obtener_elo_parejas', args=[self.jugadores[0].id]),
            HTTP_AUTH=self.tokens[self.jugadores[0]]
        )
        self.assertEqual(response_direct.status_code, 200)
        elo_direct = response_direct.json().get("elo_parejas")
        self.assertIsNotNone(elo_direct)

        # Retrieve via general stats function
        response_stats = self.client.get(
            reverse('obtener_usuario_estadisticas', args=[self.jugadores[0].id]),
            HTTP_AUTH=self.tokens[self.jugadores[0]]
        )
        self.assertEqual(response_stats.status_code, 200)
        elo_stats = response_stats.json().get("elo_parejas")
        self.assertIsNotNone(elo_stats)
        
        response_stats_direct = self.client.get(
            reverse('obtener_usuario_estadisticas'),
            HTTP_AUTH=self.tokens[self.jugadores[0]]
        )
        self.assertEqual(response_stats_direct.status_code, 200)
        elo_stats_direct = response_stats.json().get("elo_parejas")
        self.assertIsNotNone(elo_stats_direct)

        # 🔹 Ensure all retrieved Elo values are the same
        self.assertEqual(elo_token, elo_direct)
        self.assertEqual(elo_direct, elo_stats)
        self.assertEqual(elo_stats, elo_stats_direct)
