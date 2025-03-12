from django.test import TestCase
from django.urls import reverse
from partidas.models import Partida2v2  # Updated for 2v2 matches
from usuarios.models import Usuario
import json


class Partida2v2TestCase(TestCase):

    def setUp(self):
        """Setup before each test - Create users and a 2v2 match."""
        self.jugadores = [
            Usuario.objects.create(nombre=f"Jugador{i}", correo=f"jugador{i}@example.com", contrasegna="1234")
            for i in range(1, 9)  # Create 8 players
        ]

    def test_crear_partida_2v2(self):
        """Test creating a 2v2 match."""

        request_data = {
            "equipo_1_jugador_1": self.jugadores[0].id,
            "equipo_1_jugador_2": self.jugadores[1].id,
            "equipo_2_jugador_1": self.jugadores[2].id,
            "equipo_2_jugador_2": self.jugadores[3].id
        }

        create_response = self.client.post(
            reverse('crear_partida_2v2'),
            data=json.dumps(request_data),
            content_type="application/json"
        )

        self.assertEqual(create_response.status_code, 201)  # Ensure match was created

        partida_id = create_response.json().get("partida_id")
        self.assertIsNotNone(partida_id)  # Ensure match ID is returned

        # Verify match exists in database
        partida_db = Partida2v2.objects.get(id=partida_id)
        self.assertEqual(partida_db.estado_partida, "EN_JUEGO")

    def test_obtener_estado_partida_2v2(self):
        """Test retrieving the state of a 2v2 match."""

        request_data = {
            "equipo_1_jugador_1": self.jugadores[0].id,
            "equipo_1_jugador_2": self.jugadores[1].id,
            "equipo_2_jugador_1": self.jugadores[2].id,
            "equipo_2_jugador_2": self.jugadores[3].id
        }

        create_response = self.client.post(
            reverse('crear_partida_2v2'),
            data=json.dumps(request_data),
            content_type="application/json"
        )

        self.assertEqual(create_response.status_code, 201)

        partida_id = create_response.json().get("partida_id")
        self.assertIsNotNone(partida_id)

        # Retrieve match state
        estado_response = self.client.get(reverse('obtener_estado_partida_2v2', args=[partida_id]))
        self.assertEqual(estado_response.status_code, 200)

        estado_data = estado_response.json()

        # Ensure match data contains correct players
        self.assertIn(self.jugadores[0].nombre, estado_data["equipo_1"])
        self.assertIn(self.jugadores[2].nombre, estado_data["equipo_2"])

    def test_cambiar_estado_partida_2v2(self):
        """Test changing the match state in a 2v2 game."""

        # Create an active 2v2 match
        partida = Partida2v2.objects.create(
            equipo_1_jugador_1=self.jugadores[0], equipo_1_jugador_2=self.jugadores[1],
            equipo_2_jugador_1=self.jugadores[2], equipo_2_jugador_2=self.jugadores[3],
            estado_partida="EN_JUEGO"
        )

        # Simulate JSON request to finalize match with team 1 as winner
        request_data = json.dumps({"estado": "FINALIZADO", "equipo_ganador": 1})
        response = self.client.post(
            reverse('cambiar_estado_partida_2v2', args=[partida.id]),
            request_data,
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)

        # Refresh from database and validate changes
        partida.refresh_from_db()
        self.assertEqual(partida.estado_partida, "FINALIZADO")
        self.assertEqual(partida.equipo_ganador, 1)

    def test_rachas_y_elo_parejas(self):
        """Test team-based match state changes, win streak updates, and Elo adjustments."""

        # 🔹 Team 1 wins 4 consecutive matches
        for _ in range(4):
            partida = Partida2v2.objects.create(
                equipo_1_jugador_1=self.jugadores[0], equipo_1_jugador_2=self.jugadores[1],
                equipo_2_jugador_1=self.jugadores[2], equipo_2_jugador_2=self.jugadores[3],
                estado_partida="EN_JUEGO"
            )

            request_data = json.dumps({"estado": "FINALIZADO", "equipo_ganador": 1})
            response = self.client.post(
                reverse('cambiar_estado_partida_2v2', args=[partida.id]),
                request_data,
                content_type="application/json"
            )

            self.assertEqual(response.status_code, 200)

            # Refresh stats
            for jugador in self.jugadores[:4]:  # Players in the match
                jugador.refresh_from_db()

            # Ensure streak is increasing for winners
            racha_actual = self.client.get(reverse('obtener_racha_actual', args=[self.jugadores[0].id])).json()["racha_victorias"]
            self.assertEqual(racha_actual, _ + 1)

        # 🔹 Team 2 wins a match, breaking streak
        partida = Partida2v2.objects.create(
            equipo_1_jugador_1=self.jugadores[0], equipo_1_jugador_2=self.jugadores[1],
            equipo_2_jugador_1=self.jugadores[2], equipo_2_jugador_2=self.jugadores[3],
            estado_partida="EN_JUEGO"
        )

        request_data = json.dumps({"estado": "FINALIZADO", "equipo_ganador": 2})
        response = self.client.post(
            reverse('cambiar_estado_partida_2v2', args=[partida.id]),
            request_data,
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)

        # Refresh stats
        for jugador in self.jugadores[:4]:  
            jugador.refresh_from_db()

        # Ensure streak resets but longest streak remains
        racha_actual = self.client.get(reverse('obtener_racha_actual', args=[self.jugadores[0].id])).json()["racha_victorias"]
        mayor_racha = self.client.get(reverse('obtener_racha_mas_larga', args=[self.jugadores[0].id])).json()["mayor_racha_victorias"]
        self.assertEqual(racha_actual, 0)
        self.assertEqual(mayor_racha, 4)

        # 🔹 Check Elo updates
        elo_antes = self.jugadores[0].elo_parejas
        partida = Partida2v2.objects.create(
            equipo_1_jugador_1=self.jugadores[0], equipo_1_jugador_2=self.jugadores[1],
            equipo_2_jugador_1=self.jugadores[2], equipo_2_jugador_2=self.jugadores[3],
            estado_partida="EN_JUEGO"
        )

        request_data = json.dumps({"estado": "FINALIZADO", "equipo_ganador": 1})
        response = self.client.post(
            reverse('cambiar_estado_partida_2v2', args=[partida.id]),
            request_data,
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        self.jugadores[0].refresh_from_db()
        self.assertGreater(self.jugadores[0].elo_parejas, elo_antes)  # Elo should increase

