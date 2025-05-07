from django.db import models

class Tapete(models.Model):
    id = models.AutoField(primary_key=True)  # Explicitly define the ID field
    name = models.CharField(max_length=255)  # Name of the card mat
    file_path = models.CharField(max_length=500)  # Path to the card mat image

    def __str__(self):
        return self.name 