from django.test import TestCase
from django.urls import reverse
from utils.jwt_auth import generar_token  # Assuming this is the utility to generate tokens
from usuarios.models import Usuario, SolicitudAmistad

class TestTopEloForFriends(TestCase):

    def setUp(self):
        """
        Set up a test environment with users, Elo rankings, and friendships.
        """
        # Create users with different Elo rankings
        self.user1 = Usuario.objects.create(nombre="user1", correo="user1@example.com", contrasegna="password", elo=1500, elo_parejas=1400)
        self.user2 = Usuario.objects.create(nombre="user2", correo="user2@example.com", contrasegna="password", elo=1600, elo_parejas=1500)
        self.user3 = Usuario.objects.create(nombre="user3", correo="user3@example.com", contrasegna="password", elo=1400, elo_parejas=1450)
        self.user4 = Usuario.objects.create(nombre="user4", correo="user4@example.com", contrasegna="password", elo=1550, elo_parejas=1600)
        self.user5 = Usuario.objects.create(nombre="user5", correo="user5@example.com", contrasegna="password", elo=1700, elo_parejas=1650)

        # Create a test user who will have friends
        self.test_user = Usuario.objects.create(nombre="test_user", correo="test_user@example.com", contrasegna="password", elo=1800, elo_parejas=1750)

        # Generate token for test_user
        self.token_test_user = generar_token(self.test_user)

        # Simulate friendship creation
        self.user1.amigos.add(self.test_user)
        self.user2.amigos.add(self.test_user)
        self.user3.amigos.add(self.test_user)

        # Create friendship requests (user4 and user5 are not friends with the test_user)
        SolicitudAmistad.objects.create(emisor=self.user4, receptor=self.test_user)
        SolicitudAmistad.objects.create(emisor=self.user5, receptor=self.test_user)

    def test_top_elo_amigos(self):
        """
        Test that the top Elo rankings only include friends, and are ordered correctly.
        """
        response = self.client.get(reverse("obtener_top_elo_amigos"), HTTP_AUTH=self.token_test_user)

        self.assertEqual(response.status_code, 200)

        top_elo_players = response.json().get("top_elo_players")
        
        # Make sure only 3 friends are included
        self.assertEqual(len(top_elo_players), 4)

        # Check that players are ordered by Elo, highest first
        self.assertEqual(top_elo_players[0]['elo'], 1800)  # test_user has the highest Elo
        self.assertEqual(top_elo_players[1]['elo'], 1600)  # user2 has Elo 1600
        self.assertEqual(top_elo_players[2]['elo'], 1500)  # user1 has Elo 1500
        self.assertEqual(top_elo_players[3]['elo'], 1400)  # user3 has Elo 1400

    def test_top_elo_parejas_amigos(self):
        """
        Test that the top Elo parejas rankings only include friends, and are ordered correctly.
        """
        response = self.client.get(reverse("obtener_top_elo_parejas_amigos"), HTTP_AUTH=self.token_test_user)
        self.assertEqual(response.status_code, 200)

        # Check that the returned friends' Elo parejas rankings are sorted in descending order
        top_elo_parejas_players = response.json().get("top_elo_parejas_players")
        
        # Make sure only 3 friends are included
        self.assertEqual(len(top_elo_parejas_players), 4)

        # Check that players are ordered by Elo parejas, highest first
        self.assertEqual(top_elo_parejas_players[0]['elo_parejas'], 1750)  # test_user has the highest elo_parejas
        self.assertEqual(top_elo_parejas_players[1]['elo_parejas'], 1500)  # user2 has Elo parejas 1500
        self.assertEqual(top_elo_parejas_players[2]['elo_parejas'], 1450)  # user3 has Elo parejas 1450
        self.assertEqual(top_elo_parejas_players[3]['elo_parejas'], 1400)  # user1 has Elo parejas 1400
