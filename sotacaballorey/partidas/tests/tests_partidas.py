from django.test import TestCase
from django.urls import reverse
from partidas.models import Partida  # Import Partida from partidas app
from usuarios.models import Usuario  # Import Usuario from usuarios app
from partidas.views import cambiar_estado_partida, barajar_cartas, crear_partida  # Import methods directly
from usuarios.views import obtener_racha_actual, obtener_racha_mas_larga, iniciar_sesion  # Import user stats methods
import json
from django.http import JsonResponse


class PartidaTestCase(TestCase):

    def setUp(self):
        """Setup before each test - Create users and a match."""
        self.jugador1 = Usuario.objects.create(
            nombre="Carlos",
            correo="carlos@example.com",
            contrasegna="1234"
        )

        self.jugador2 = Usuario.objects.create(
            nombre="Elena",
            correo="elena@example.com",
            contrasegna="1234"
        )

    def test_crear_partida(self):
        """Test creating a match using the crear_partida method."""

        request_data = {"jugador1_id": self.jugador1.id, "jugador2_id": self.jugador2.id}
        create_response = self.client.post(
            reverse('crear_partida'),
            data=json.dumps(request_data),
            content_type="application/json"
        )

        self.assertEqual(create_response.status_code, 201)  # Ensure match was created

        # Extract partida_id from response
        partida_id = create_response.json().get("partida_id")
        self.assertIsNotNone(partida_id)  # Ensure partida_id is returned

        # Verify match exists in database
        partida_db = Partida.objects.get(id=partida_id)
        self.assertEqual(partida_db.estado_partida, "EN_JUEGO")

    def test_barajar_cartas(self):
        """Test if cards are shuffled and distributed correctly using obtener_estado_partida."""

        request_data = {"jugador1_id": self.jugador1.id, "jugador2_id": self.jugador2.id}
        create_response = self.client.post(
            reverse('crear_partida'),
            data=json.dumps(request_data),
            content_type="application/json"
        )

        self.assertEqual(create_response.status_code, 201)  # Ensure match creation was successful

        partida_id = create_response.json().get("partida_id")
        self.assertIsNotNone(partida_id)  # Ensure partida_id exists

        # Retrieve match state using obtener_estado_partida
        estado_response = self.client.get(reverse('obtener_estado_partida', args=[partida_id]))
        self.assertEqual(estado_response.status_code, 200)  # Ensure request was successful

        estado_data = estado_response.json()

        # Ensure match has 5 cards for each player
        self.assertEqual(len(estado_data["cartas_jugador_1"]), 5)
        self.assertEqual(len(estado_data["cartas_jugador_2"]), 5)

        # Ensure triumph suit is correctly assigned
        self.assertIn(estado_data["triunfo_palo"], ["oros", "copas", "espadas", "bastos"])

    def test_cambiar_estado_partida(self):
        """Test changing the match state using JSON POST requests."""

        # Create an active match
        partida = Partida.objects.create(jugador_1=self.jugador1, jugador_2=self.jugador2, estado_partida="EN_JUEGO")

        # Simulate JSON request to change match state
        request_data = json.dumps({"estado": "FINALIZADO", "ganador_id": self.jugador1.id})
        response = self.client.post(
            reverse('cambiar_estado_partida', args=[partida.id]),
            request_data,
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)

        # Refresh from database and validate changes
        partida.refresh_from_db()
        self.assertEqual(partida.estado_partida, "FINALIZADO")
        self.assertEqual(partida.ganador, self.jugador1)

    def test_rachas(self):
        """Test match state changes, win streak resets, and longest streak updates correctly."""

        # 🔹 Player 1 wins 4 consecutive matches using JSON POST requests
        for _ in range(4):
            partida = Partida.objects.create(jugador_1=self.jugador1, jugador_2=self.jugador2, estado_partida="EN_JUEGO")

            # Simulate JSON request
            request_data = json.dumps({"estado": "FINALIZADO", "ganador_id": self.jugador1.id})
            request = self.client.post(
                reverse('cambiar_estado_partida', args=[partida.id]),
                request_data,
                content_type="application/json"
            )

            self.assertEqual(request.status_code, 200)

            # Refresh stats
            self.jugador1.refresh_from_db()
            self.jugador2.refresh_from_db()

            # Ensure streak is increasing
            racha_actual = self.client.get(reverse('obtener_racha_actual', args=[self.jugador1.id])).json()["racha_victorias"]
            mayor_racha = self.client.get(reverse('obtener_racha_mas_larga', args=[self.jugador1.id])).json()["mayor_racha_victorias"]

            self.assertEqual(racha_actual, _ + 1)
            self.assertEqual(mayor_racha, _ + 1)  # Longest streak should match streak

        # 🔹 Player 1 loses a match
        partida = Partida.objects.create(jugador_1=self.jugador1, jugador_2=self.jugador2, estado_partida="EN_JUEGO")
        request_data = json.dumps({"estado": "FINALIZADO", "ganador_id": self.jugador2.id})
        request = self.client.post(reverse('cambiar_estado_partida', args=[partida.id]), request_data, content_type="application/json")
        self.assertEqual(request.status_code, 200)

        # Refresh stats
        self.jugador1.refresh_from_db()
        self.jugador2.refresh_from_db()

        # Ensure streak resets but longest streak remains
        racha_actual = self.client.get(reverse('obtener_racha_actual', args=[self.jugador1.id])).json()["racha_victorias"]
        mayor_racha = self.client.get(reverse('obtener_racha_mas_larga', args=[self.jugador1.id])).json()["mayor_racha_victorias"]
        self.assertEqual(racha_actual, 0)
        self.assertEqual(mayor_racha, 4)  # Longest streak should stay at 4

        # 🔹 Player 1 wins 6 matches in a row (breaking previous longest streak of 4)
        for _ in range(6):


            partida = Partida.objects.create(jugador_1=self.jugador1, jugador_2=self.jugador2, estado_partida="EN_JUEGO")
            # Simulate JSON request
            request_data = json.dumps({"estado": "FINALIZADO", "ganador_id": self.jugador1.id})
            request = self.client.post(reverse('cambiar_estado_partida', args=[partida.id]), request_data, content_type="application/json")
            self.assertEqual(request.status_code, 200)


            # Refresh stats
            self.jugador1.refresh_from_db()


            # Ensure streak increases correctly
            racha_actual = self.client.get(reverse('obtener_racha_actual', args=[self.jugador1.id])).json()["racha_victorias"]
            self.assertEqual(racha_actual, _ + 1)

        # Refresh stats after the final win
        self.jugador1.refresh_from_db()

        # 🔹 Ensure longest streak is updated when breaking the previous one (4 → 6)
        mayor_racha = self.client.get(reverse('obtener_racha_mas_larga', args=[self.jugador1.id])).json()["mayor_racha_victorias"]
        self.assertEqual(mayor_racha, 6)

        # 🔹 Test total matches played
        total_partidas = self.client.get(reverse('obtener_total_partidas', args=[self.jugador1.id])).json()["total_partidas"]
        self.assertEqual(total_partidas, 4 + 1 + 6)  # Total should be 11 (4 wins, 1 loss, 6 wins)

        # 🔹 Test win percentage
        win_percentage = self.client.get(reverse('obtener_porcentaje_victorias', args=[self.jugador1.id])).json()["porcentaje_victorias"]
        expected_win_percentage = (10 / 11) * 100  # 10 wins out of 11 matches
        self.assertAlmostEqual(win_percentage, expected_win_percentage, places=1)


        # 🔹 Test loss percentage
        loss_percentage = self.client.get(reverse('obtener_porcentaje_derrotas', args=[self.jugador1.id])).json()["porcentaje_derrotas"]
        expected_loss_percentage = (1 / 11) * 100  # 1 loss out of 11 matches
        self.assertAlmostEqual(loss_percentage, expected_loss_percentage, places=1)





        # 🔹 Test overall statistics
        """overall_stats = self.client.get(reverse('obtener_usuario_estadisticas', args=[self.jugador1.id])).json()
        self.assertEqual(overall_stats["victorias"], 10)
        self.assertEqual(overall_stats["derrotas"], 1)
        self.assertEqual(overall_stats["racha_victorias"], 6)
        self.assertEqual(overall_stats["mayor_racha_victorias"], 6)
        self.assertEqual(overall_stats["total_partidas"], 11)
        self.assertAlmostEqual(overall_stats["porcentaje_victorias"], expected_win_percentage, places=1)
        self.assertAlmostEqual(overall_stats["porcentaje_derrotas"], expected_loss_percentage, places=1)"""
