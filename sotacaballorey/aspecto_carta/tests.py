# yourapp/tests/test_populate_skins.py
from django.test import TransactionTestCase
from aspecto_carta.models import CardSkin
import json
import os
from django.core.management import call_command


class TestPopulateSkins(TransactionTestCase):
    databases = {'default'}  # Use the default (production) database
    
    fixtures = [
            'aspecto_carta/fixtures/initial_data.json',
            'tapete/fixtures/initial_data.json'
        ]
    for fixture in fixtures:
            call_command('loaddata', fixture)

    def test_populate_skins(self):
        # Load the skins from the JSON fixture to check against the database
        with open('aspecto_carta/fixtures/initial_data.json', 'r') as file:
            skins_data = json.load(file)
            
        # Check that the skins in the database match those in the JSON
        for skin in skins_data:
            # The fields are inside the 'fields' key in the fixture data
            skin_name = skin["fields"]["name"]
            skin_file_path = skin["fields"]["file_path"]

            # Query the database to check if the skin exists
            skin_in_db = CardSkin.objects.filter(name=skin_name).first()
            self.assertIsNotNone(skin_in_db, f"Skin '{skin_name}' not found in the database")
            self.assertEqual(skin_in_db.file_path, skin_file_path, f"File path mismatch for skin '{skin_name}'")
