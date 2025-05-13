# yourapp/tests/test_unlock_skins.py
from django.test import TestCase
from aspecto_carta.models import CardSkin
from tapete.models import Tapete
from usuarios.models import Usuario
from django.core.management import call_command

class TestUnlockSkinsAndTapetes(TestCase):
    
    def setUp(self):
        """Create the default skins and tapetes that will be unlocked"""
        # Create the default skins
        fixtures = [
            'aspecto_carta/fixtures/initial_data.json',
            'tapete/fixtures/initial_data.json'
        ]
        for fixture in fixtures:
            call_command('loaddata', fixture)

        self.default_skin = CardSkin.objects.get(name="Default")
        self.poker_skin = CardSkin.objects.get(name="Poker")
        self.paint_skin = CardSkin.objects.get(name="Paint")
        self.default_tapete = Tapete.objects.get(name="Default")
        self.red_black_tapete = Tapete.objects.get(name="Rojo-negro")
        self.blue_silver_tapete = Tapete.objects.get(name="Azul-plata")
        self.red_gold_tapete = Tapete.objects.get(name="Rojo-dorado")


    def test_unlock_skins_for_guiri(self):
        """Test that a 'Guiri' user gets the correct skins and tapetes unlocked"""
        # Create a 'Guiri' user with an elo value of 0
        user = Usuario.objects.create(
            nombre="Guiri User",
            correo="guiri@example.com",
            contrasegna="password",
            elo=0,
            elo_rank="guiri"
        )
        
        # Save the user (this will trigger the unlocking of skins and tapetes)
        user.save()

        # Check the unlocked skins and tapetes
        self.assertIn(self.default_skin, user.unlocked_skins.all())  # Default skin should be unlocked
        self.assertIn(self.default_tapete, user.unlocked_tapetes.all())  # Default tapete should be unlocked
        self.assertNotIn(self.poker_skin, user.unlocked_skins.all())  # Poker skin should NOT be unlocked for Guiri
        self.assertNotIn(self.paint_skin, user.unlocked_skins.all())  # Paint skin should NOT be unlocked for Guiri
        self.assertNotIn(self.red_black_tapete, user.unlocked_tapetes.all())  # Red-black tapete should NOT be unlocked for Guiri
        self.assertNotIn(self.blue_silver_tapete, user.unlocked_tapetes.all())  # Blue-silver tapete should NOT be unlocked for Guiri
        self.assertNotIn(self.red_gold_tapete, user.unlocked_tapetes.all())  # Red-gold tapete should NOT be unlocked for Guiri

    def test_unlock_skins_for_casual(self):
        """Test that a 'Casual' user gets the correct skins and tapetes unlocked"""
        # Create a 'Casual' user with an elo value of 1200
        user = Usuario.objects.create(
            nombre="Casual User",
            correo="casual@example.com",
            contrasegna="password",
            elo=1200,
            elo_rank="casual"
        )
        
        # Save the user (this will trigger the unlocking of skins and tapetes)
        user.save()

        # Check the unlocked skins and tapetes
        self.assertIn(self.default_skin, user.unlocked_skins.all())  # Default skin should be unlocked
        self.assertNotIn(self.poker_skin, user.unlocked_skins.all())   # Poker skin should NOT be unlocked
        self.assertIn(self.default_tapete, user.unlocked_tapetes.all())  # Default tapete should be unlocked
        self.assertNotIn(self.paint_skin, user.unlocked_skins.all())  # Paint skin should NOT be unlocked for Casual
        self.assertIn(self.red_black_tapete, user.unlocked_tapetes.all())  # Red-black tapete should be unlocked for Casual
        self.assertNotIn(self.blue_silver_tapete, user.unlocked_tapetes.all())  # Blue-silver tapete should NOT be unlocked for Casual
        self.assertNotIn(self.red_gold_tapete, user.unlocked_tapetes.all())  # Red-gold tapete should NOT be unlocked for Casual  

    def test_unlock_skins_for_parroquiano(self):
        """Test that a 'Parroquiano' user gets the correct skins and tapetes unlocked"""
        # Create a 'Parroquiano' user with an elo value of 1600
        user = Usuario.objects.create(
            nombre="Parroquiano User",
            correo="parroquiano@example.com",
            contrasegna="password",
            elo=1600,
            elo_rank="parroquiano"
        )
        
        # Save the user (this will trigger the unlocking of skins and tapetes)
        user.save()

        # Check the unlocked skins and tapetes
        self.assertIn(self.default_skin, user.unlocked_skins.all())  # Default skin should be unlocked
        self.assertIn(self.poker_skin, user.unlocked_skins.all())   # Poker skin should be unlocked
        self.assertIn(self.default_tapete, user.unlocked_tapetes.all())  # Default tapete should be unlocked
        self.assertNotIn(self.paint_skin, user.unlocked_skins.all())  # Paint skin should NOT be unlocked for Parroquiano
        self.assertIn(self.red_black_tapete, user.unlocked_tapetes.all())  # Red-black tapete should be unlocked for Parroquiano
        self.assertNotIn(self.blue_silver_tapete, user.unlocked_tapetes.all())  # Blue-silver tapete should NOT be unlocked for Parroquiano
        self.assertNotIn(self.red_gold_tapete, user.unlocked_tapetes.all())  # Red-gold tapete should NOT be unlocked for Parroquiano

    def test_unlock_skins_for_octogenario(self):
        """Test that a 'Octogenario' user gets the correct skins and tapetes unlocked"""
        # Create a 'Octogenario' user with an elo value of 2100
        user = Usuario.objects.create(
            nombre="Octogenario User",
            correo="octogenario@example.com",
            contrasegna="password",
            elo=2100,
            elo_rank="octogenario"
        )
        
        # Save the user (this will trigger the unlocking of skins and tapetes)
        user.save()

        # Check the unlocked skins and tapetes
        self.assertIn(self.default_skin, user.unlocked_skins.all())  # Default skin should be unlocked
        self.assertIn(self.poker_skin, user.unlocked_skins.all())   # Poker skin should be unlocked
        self.assertIn(self.default_tapete, user.unlocked_tapetes.all())  # Default tapete should be unlocked
        self.assertIn(self.blue_silver_tapete, user.unlocked_tapetes.all())  # Blue-silver tapete should be unlocked for Octogenario
        self.assertIn(self.red_black_tapete, user.unlocked_tapetes.all())  # Red-black tapete should be unlocked for Octogenario
        self.assertNotIn(self.red_gold_tapete, user.unlocked_tapetes.all())  # Red-gold tapete should NOT be unlocked for Octogenario
        self.assertNotIn(self.paint_skin, user.unlocked_skins.all())  # Paint skin should NOT be unlocked for Octogenario
  
    

    def test_unlock_skins_for_leyenda(self):
        """Test that a 'Leyenda' user gets the correct skins and tapetes unlocked"""
        # Create a 'Leyenda' user with an elo value of 2700
        user = Usuario.objects.create(
            nombre="Leyenda User",
            correo="leyenda@example.com",
            contrasegna="password",
            elo=2700,
            elo_rank="leyenda"
        )
        
        # Save the user (this will trigger the unlocking of skins and tapetes)
        user.save()

        # Check the unlocked skins and tapetes
        self.assertIn(self.default_skin, user.unlocked_skins.all())  # Default skin should be unlocked
        self.assertIn(self.paint_skin, user.unlocked_skins.all())   # Paint skin should be unlocked
        self.assertIn(self.default_tapete, user.unlocked_tapetes.all())  # Default tapete should be unlocked
        self.assertIn(self.red_black_tapete, user.unlocked_tapetes.all())  # Red-black tapete should be unlocked for Leyenda
        self.assertIn(self.red_gold_tapete, user.unlocked_tapetes.all())  # Red-gold tapete should be unlocked for Leyenda
        self.assertIn(self.poker_skin, user.unlocked_skins.all())  # Poker skin should NOT be unlocked for Leyenda
        self.assertIn(self.blue_silver_tapete, user.unlocked_tapetes.all())  # Blue-silver tapete should NOT be unlocked for Leyenda

    def tearDown(self):
        """Clean up after tests"""
        # Delete the test objects (skins, tapetes, users)
        CardSkin.objects.all().delete()
        Tapete.objects.all().delete()
        Usuario.objects.all().delete()
