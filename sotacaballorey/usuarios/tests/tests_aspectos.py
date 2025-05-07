from django.test import TestCase
from django.urls import reverse
from aspecto_carta.models import CardSkin
from dorso_carta.models import CardBack
from tapete.models import Tapete
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
        
        # Create 3 card mats
        self.tapete1 = Tapete.objects.create(name="Green Felt", file_path="/images/tapetes/green_felt.png")
        self.tapete2 = Tapete.objects.create(name="Blue Velvet", file_path="/images/tapetes/blue_velvet.png")
        self.tapete3 = Tapete.objects.create(name="Red Leather", file_path="/images/tapetes/red_leather.png")
        
        # Create a test user
        self.user = Usuario.objects.create(nombre="Test Player")
        
        # Define the URLs for unlocking and retrieving
        self.unlock_skin_url = reverse('unlock_skin', kwargs={'user_id': self.user.id})
        self.unlock_back_url = reverse('unlock_back', kwargs={'user_id': self.user.id})
        self.unlock_tapete_url = reverse('unlock_tapete', kwargs={'user_id': self.user.id})
        self.get_unlocked_items_url = reverse('get_unlocked_items', kwargs={'user_id': self.user.id})
        self.get_equipped_items_url = reverse('get_equipped_items', kwargs={'user_id': self.user.id})
        
        self.get_card_skin_id_url = reverse('get_card_skin_id_from_name')
        self.get_card_back_id_url = reverse('get_card_back_id_from_name')
        self.get_tapete_id_url = reverse('get_tapete_id_from_name')
    
    def test_add_and_unlock_card_skins_backs_and_tapetes(self):
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

        # Test adding and retrieving all card mats
        response = self.client.get(reverse('get_all_tapetes'))
        self.assertEqual(response.status_code, 200)
        
        # Check the tapetes are in the response
        tapetes_data = json.loads(response.content)['tapetes']
        self.assertEqual(len(tapetes_data), 3)
        self.assertIn(self.tapete1.name, [tapete['name'] for tapete in tapetes_data])
        self.assertIn(self.tapete2.name, [tapete['name'] for tapete in tapetes_data])
        self.assertIn(self.tapete3.name, [tapete['name'] for tapete in tapetes_data])
        
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

        # Unlock 2 tapetes for the test user
        response = self.client.post(self.unlock_tapete_url, json.dumps({"tapete_id": self.tapete1.id}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        response = self.client.post(self.unlock_tapete_url, json.dumps({"tapete_id": self.tapete2.id}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        
        # Retrieve the unlocked items for the test user
        response = self.client.get(self.get_unlocked_items_url)
        self.assertEqual(response.status_code, 200)
        
        unlocked_data = json.loads(response.content)
        unlocked_skins = unlocked_data['unlocked_skins']
        unlocked_backs = unlocked_data['unlocked_backs']
        unlocked_tapetes = unlocked_data['unlocked_tapetes']
        
        # Check that the unlocked skins are correct
        self.assertEqual(len(unlocked_skins), 2)
        self.assertIn(self.skin1.name, [skin['name'] for skin in unlocked_skins])
        self.assertIn(self.skin2.name, [skin['name'] for skin in unlocked_skins])
        
        # Check that the unlocked backs are correct
        self.assertEqual(len(unlocked_backs), 2)
        self.assertIn(self.back1.name, [back['name'] for back in unlocked_backs])
        self.assertIn(self.back2.name, [back['name'] for back in unlocked_backs])

        # Check that the unlocked tapetes are correct
        self.assertEqual(len(unlocked_tapetes), 2)
        self.assertIn(self.tapete1.name, [tapete['name'] for tapete in unlocked_tapetes])
        self.assertIn(self.tapete2.name, [tapete['name'] for tapete in unlocked_tapetes])
        
    def test_get_card_skin_id_from_name(self):
        # Test retrieving CardSkin ID by name
        response = self.client.get(self.get_card_skin_id_url, {'name': 'Flame Design'})
        self.assertEqual(response.status_code, 200)
        
        # Check if the response contains the correct ID and name
        response_data = json.loads(response.content)
        self.assertEqual(response_data['id'], self.skin1.id)
        self.assertEqual(response_data['name'], 'Flame Design')

        # Test for a non-existing CardSkin
        response = self.client.get(self.get_card_skin_id_url, {'name': 'NonExistent Skin'})
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], "CardSkin not found")

    def test_get_card_back_id_from_name(self):
        # Test retrieving CardBack ID by name
        response = self.client.get(self.get_card_back_id_url, {'name': 'Fire Back'})
        self.assertEqual(response.status_code, 200)
        
        # Check if the response contains the correct ID and name
        response_data = json.loads(response.content)
        self.assertEqual(response_data['id'], self.back1.id)
        self.assertEqual(response_data['name'], 'Fire Back')

        # Test for a non-existing CardBack
        response = self.client.get(self.get_card_back_id_url, {'name': 'NonExistent Back'})
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], "CardBack not found")

    def test_get_tapete_id_from_name(self):
        # Test retrieving Tapete ID by name
        response = self.client.get(self.get_tapete_id_url, {'name': 'Green Felt'})
        self.assertEqual(response.status_code, 200)
        
        # Check if the response contains the correct ID and name
        response_data = json.loads(response.content)
        self.assertEqual(response_data['id'], self.tapete1.id)
        self.assertEqual(response_data['name'], 'Green Felt')

        # Test for a non-existing Tapete
        response = self.client.get(self.get_tapete_id_url, {'name': 'NonExistent Tapete'})
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], "Tapete not found")

    def test_get_equipped_items(self):
        # First unlock some items
        self.client.post(self.unlock_skin_url, json.dumps({"skin_id": self.skin1.id}), content_type="application/json")
        self.client.post(self.unlock_back_url, json.dumps({"back_id": self.back1.id}), content_type="application/json")
        self.client.post(self.unlock_tapete_url, json.dumps({"tapete_id": self.tapete1.id}), content_type="application/json")
        
        # Initially, no items should be equipped
        response = self.client.get(self.get_equipped_items_url)
        self.assertEqual(response.status_code, 200)
        equipped_data = json.loads(response.content)
        self.assertIsNone(equipped_data['equipped_skin'])
        self.assertIsNone(equipped_data['equipped_back'])
        self.assertIsNone(equipped_data['equipped_tapete'])
        
        # Equip items
        self.client.post(reverse('equip_skin', kwargs={'user_id': self.user.id}), 
                        json.dumps({"skin_id": self.skin1.id}), 
                        content_type="application/json")
        self.client.post(reverse('equip_back', kwargs={'user_id': self.user.id}), 
                        json.dumps({"back_id": self.back1.id}), 
                        content_type="application/json")
        self.client.post(reverse('equip_tapete', kwargs={'user_id': self.user.id}), 
                        json.dumps({"tapete_id": self.tapete1.id}), 
                        content_type="application/json")
        
        # Check equipped items
        response = self.client.get(self.get_equipped_items_url)
        self.assertEqual(response.status_code, 200)
        equipped_data = json.loads(response.content)
        
        # Verify equipped skin
        self.assertIsNotNone(equipped_data['equipped_skin'])
        self.assertEqual(equipped_data['equipped_skin']['id'], self.skin1.id)
        self.assertEqual(equipped_data['equipped_skin']['name'], self.skin1.name)
        self.assertEqual(equipped_data['equipped_skin']['file_path'], self.skin1.file_path)
        
        # Verify equipped back
        self.assertIsNotNone(equipped_data['equipped_back'])
        self.assertEqual(equipped_data['equipped_back']['id'], self.back1.id)
        self.assertEqual(equipped_data['equipped_back']['name'], self.back1.name)
        self.assertEqual(equipped_data['equipped_back']['file_path'], self.back1.file_path)
        
        # Verify equipped tapete
        self.assertIsNotNone(equipped_data['equipped_tapete'])
        self.assertEqual(equipped_data['equipped_tapete']['id'], self.tapete1.id)
        self.assertEqual(equipped_data['equipped_tapete']['name'], self.tapete1.name)
        self.assertEqual(equipped_data['equipped_tapete']['file_path'], self.tapete1.file_path)
        
        # Test with non-existent user
        response = self.client.get(reverse('get_equipped_items', kwargs={'user_id': 999}))
        self.assertEqual(response.status_code, 404)
        error_data = json.loads(response.content)
        self.assertEqual(error_data['error'], "User not found")

    def tearDown(self):
        # Clean up any data after each test
        self.user.delete()
        self.skin1.delete()
        self.skin2.delete()
        self.skin3.delete()
        self.back1.delete()
        self.back2.delete()
        self.back3.delete()
        self.tapete1.delete()
        self.tapete2.delete()
        self.tapete3.delete()
