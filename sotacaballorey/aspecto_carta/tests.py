# yourapp/tests/test_populate_skins.py
from django.test import TransactionTestCase
from aspecto_carta.models import CardSkin
import json
import os

class TestPopulateSkins(TransactionTestCase):
    databases = {'default'}  # Use the default (production) database
    
    def test_populate_skins(self):
        # Load the skins from the JSON fixture to check against the database
        with open('aspecto_carta/fixtures/initial_data.json', 'r') as file:
            skins_data = json.load(file)
            
        # Print the entire CardSkin table first
        print("\n=== CardSkin Table ===")
        for skin in CardSkin.objects.all():
            print(f"ID: {skin.id}, Name: {skin.name}, File Path: {skin.file_path}")
        print("======================\n")
        
        # Check that the skins in the database match those in the JSON
        for skin in skins_data:
            # The fields are inside the 'fields' key in the fixture data
            skin_name = skin["fields"]["name"]
            skin_file_path = skin["fields"]["file_path"]

            # Query the database to check if the skin exists
            skin_in_db = CardSkin.objects.filter(name=skin_name).first()
            self.assertIsNotNone(skin_in_db, f"Skin '{skin_name}' not found in the database")
            self.assertEqual(skin_in_db.file_path, skin_file_path, f"File path mismatch for skin '{skin_name}'")
