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


    def test_no_players2v2(self):
        """Test that the response is empty when there are no players for both Elo rankings."""
        
        # Test regular Elo ranking
        response_elo = self.client.get(reverse('obtener_top_elo'))
        self.assertEqual(response_elo.status_code, 200)
        self.assertEqual(response_elo.json()["top_elo_players"], [])

        # Test Elo Parejas ranking
        response_elo_parejas = self.client.get(reverse('obtener_top_elo_parejas'))
        self.assertEqual(response_elo_parejas.status_code, 200)
        self.assertEqual(response_elo_parejas.json()["top_elo_parejas_players"], [])

    def test_ten_players2v2(self):
        """Test that 10 players with arbitrary Elo values are correctly ordered for both Elo rankings."""
        
        players = [
            Usuario.objects.create(
                nombre=f"Player{i}",
                correo=f"player{i}@example.com",
                contrasegna="1234",
                elo=1000 + i*10,
                elo_parejas=1000 + i*15  # Different scaling for team ranking
            )
            for i in range(10)
        ]

        # Test regular Elo ranking
        response_elo = self.client.get(reverse('obtener_top_elo'))
        self.assertEqual(response_elo.status_code, 200)

        ranking_elo = response_elo.json()["top_elo_players"]
        self.assertEqual(len(ranking_elo), 10)

        # Ensure correct order (highest Elo first)
        expected_order_elo = sorted(players, key=lambda p: p.elo, reverse=True)
        for i in range(10):
            self.assertEqual(ranking_elo[i]["nombre"], expected_order_elo[i].nombre)
            self.assertEqual(ranking_elo[i]["elo"], expected_order_elo[i].elo)

        # Test Elo Parejas ranking
        response_elo_parejas = self.client.get(reverse('obtener_top_elo_parejas'))
        self.assertEqual(response_elo_parejas.status_code, 200)

        ranking_elo_parejas = response_elo_parejas.json()["top_elo_parejas_players"]
        self.assertEqual(len(ranking_elo_parejas), 10)

        # Ensure correct order for Elo Parejas
        expected_order_elo_parejas = sorted(players, key=lambda p: p.elo_parejas, reverse=True)
        for i in range(10):
            self.assertEqual(ranking_elo_parejas[i]["nombre"], expected_order_elo_parejas[i].nombre)
            self.assertEqual(ranking_elo_parejas[i]["elo_parejas"], expected_order_elo_parejas[i].elo_parejas)

    def test_twenty_one_players2v2(self):
        """Test that with 21 players, only the top 20 are returned for both Elo rankings."""
        
        players = [
            Usuario.objects.create(
                nombre=f"Player{i}",
                correo=f"player{i}@example.com",
                contrasegna="1234",
                elo=1000 + i*10,
                elo_parejas=1000 + i*15
            )
            for i in range(21)
        ]

        # Test regular Elo ranking
        response_elo = self.client.get(reverse('obtener_top_elo'))
        self.assertEqual(response_elo.status_code, 200)

        ranking_elo = response_elo.json()["top_elo_players"]
        self.assertEqual(len(ranking_elo), 20)  # Ensure no more than 20 players

        # Ensure correct order for Elo
        expected_order_elo = sorted(players, key=lambda p: p.elo, reverse=True)[:20]
        for i in range(20):
            self.assertEqual(ranking_elo[i]["nombre"], expected_order_elo[i].nombre)
            self.assertEqual(ranking_elo[i]["elo"], expected_order_elo[i].elo)

        # Test Elo Parejas ranking
        response_elo_parejas = self.client.get(reverse('obtener_top_elo_parejas'))
        self.assertEqual(response_elo_parejas.status_code, 200)

        ranking_elo_parejas = response_elo_parejas.json()["top_elo_parejas_players"]
        self.assertEqual(len(ranking_elo_parejas), 20)  # Ensure no more than 20 players

        # Ensure correct order for Elo Parejas
        expected_order_elo_parejas = sorted(players, key=lambda p: p.elo_parejas, reverse=True)[:20]
        for i in range(20):
            self.assertEqual(ranking_elo_parejas[i]["nombre"], expected_order_elo_parejas[i].nombre)
            self.assertEqual(ranking_elo_parejas[i]["elo_parejas"], expected_order_elo_parejas[i].elo_parejas)
