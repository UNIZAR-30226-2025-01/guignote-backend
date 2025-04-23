from django.test import TestCase
from django.urls import reverse
from aspecto_carta.models import CardSkin
from dorso_carta.models import CardBack
from usuarios.models import Usuario
import json

class CardSkinBackTestCase(TestCase):
    
    def setUp(self):
        # Create 3 card skins
        self.skin1 = CardSkin.objects.create(name="Flame Design", file_path="/images/skins/flame.png")
        self.skin2 = CardSkin.objects.create(name="Water Design", file_path="/images/skins/water.png")
        self.skin3 = CardSkin.objects.create(name="Earth Design", file_path="/images/skins/earth.png")
        
        # Create 3 card backs
        self.back1 = CardBack.objects.create(name="Fire Back", file_path="/images/backs/fire.png")
        self.back2 = CardBack.objects.create(name="Blue Back", file_path="/images/backs/blue.png")
        self.back3 = CardBack.objects.create(name="Golden Back", file_path="/images/backs/golden.png")
        
        # Create a test user
        self.user = Usuario.objects.create(nombre="Test Player")
        
        # Define the URLs for unlocking and retrieving
        self.unlock_skin_url = reverse('unlock_skin', kwargs={'user_id': self.user.id})
        self.unlock_back_url = reverse('unlock_back', kwargs={'user_id': self.user.id})
        self.get_unlocked_items_url = reverse('get_unlocked_items', kwargs={'user_id': self.user.id})
    
    def test_add_and_unlock_card_skins_and_back(self):
        # Test adding and retrieving all card skins
        response = self.client.get(reverse('get_all_card_skins'))
        self.assertEqual(response.status_code, 200)
        
        # Check the skins are in the response
        skins_data = json.loads(response.content)['card_skins']
        self.assertEqual(len(skins_data), 3)
        self.assertIn(self.skin1.name, [skin['name'] for skin in skins_data])
        self.assertIn(self.skin2.name, [skin['name'] for skin in skins_data])
        self.assertIn(self.skin3.name, [skin['name'] for skin in skins_data])
        
        # Test adding and retrieving all card backs
        response = self.client.get(reverse('get_all_card_backs'))
        self.assertEqual(response.status_code, 200)
        
        # Check the backs are in the response
        backs_data = json.loads(response.content)['card_backs']
        self.assertEqual(len(backs_data), 3)
        self.assertIn(self.back1.name, [back['name'] for back in backs_data])
        self.assertIn(self.back2.name, [back['name'] for back in backs_data])
        self.assertIn(self.back3.name, [back['name'] for back in backs_data])
        
        # Unlock 2 skins for the test user
        response = self.client.post(self.unlock_skin_url, json.dumps({"skin_id": self.skin1.id}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.client.post(self.unlock_skin_url, json.dumps({"skin_id": self.skin2.id}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        
        # Unlock 2 backs for the test user
        response = self.client.post(self.unlock_back_url, json.dumps({"back_id": self.back1.id}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.client.post(self.unlock_back_url, json.dumps({"back_id": self.back2.id}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        
        # Retrieve the unlocked items for the test user
        response = self.client.get(self.get_unlocked_items_url)
        self.assertEqual(response.status_code, 200)
        
        unlocked_data = json.loads(response.content)
        unlocked_skins = unlocked_data['unlocked_skins']
        unlocked_backs = unlocked_data['unlocked_backs']
        
        # Check that the unlocked skins are correct
        self.assertEqual(len(unlocked_skins), 2)
        self.assertIn(self.skin1.name, [skin['name'] for skin in unlocked_skins])
        self.assertIn(self.skin2.name, [skin['name'] for skin in unlocked_skins])
        
        # Check that the unlocked backs are correct
        self.assertEqual(len(unlocked_backs), 2)
        self.assertIn(self.back1.name, [back['name'] for back in unlocked_backs])
        self.assertIn(self.back2.name, [back['name'] for back in unlocked_backs])

    def tearDown(self):
        # Clean up any data after each test
        self.user.delete()
        self.skin1.delete()
        self.skin2.delete()
        self.skin3.delete()
        self.back1.delete()
        self.back2.delete()
        self.back3.delete()
