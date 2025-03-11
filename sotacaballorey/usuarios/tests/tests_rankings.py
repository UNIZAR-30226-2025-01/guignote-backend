from django.test import TestCase
from django.urls import reverse
from usuarios.models import Usuario
import json

class TopEloTestCase(TestCase):

    def test_no_players(self):
        """Test that the response is empty when there are no players."""
        response = self.client.get(reverse('obtener_top_elo'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["top_elo_players"], [])

    def test_ten_players(self):
        """Test that 10 players with arbitrary Elo values are correctly ordered."""
        players = [
            Usuario.objects.create(nombre=f"Player{i}", correo=f"player{i}@example.com", contrasegna="1234", elo=1000 + i*10)
            for i in range(10)
        ]

        response = self.client.get(reverse('obtener_top_elo'))
        self.assertEqual(response.status_code, 200)

        ranking = response.json()["top_elo_players"]
        self.assertEqual(len(ranking), 10)

        # Ensure correct order (highest Elo first)
        expected_order = sorted(players, key=lambda p: p.elo, reverse=True)
        for i in range(10):
            self.assertEqual(ranking[i]["nombre"], expected_order[i].nombre)
            self.assertEqual(ranking[i]["elo"], expected_order[i].elo)

    def test_twenty_one_players(self):
        """Test that with 21 players, only the top 20 are returned."""
        players = [
            Usuario.objects.create(nombre=f"Player{i}", correo=f"player{i}@example.com", contrasegna="1234", elo=1000 + i*10)
            for i in range(21)
        ]

        response = self.client.get(reverse('obtener_top_elo'))
        self.assertEqual(response.status_code, 200)

        ranking = response.json()["top_elo_players"]
        self.assertEqual(len(ranking), 20)  # Ensure no more than 20 players

        # Ensure correct order (highest Elo first)
        expected_order = sorted(players, key=lambda p: p.elo, reverse=True)[:20]
        for i in range(20):
            self.assertEqual(ranking[i]["nombre"], expected_order[i].nombre)
            self.assertEqual(ranking[i]["elo"], expected_order[i].elo)
