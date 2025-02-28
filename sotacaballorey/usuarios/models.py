from django.db import models

class Usuario(models.Model):
    nombre = models.CharField\
        (max_length=64,  blank=False, null=False, unique=True)
    correo = models.CharField\
        (max_length=320, blank=False, null=False, unique=True)
    contrasegna = models.CharField\
        (max_length=128, blank=False, null=False, unique=False)
    
    def __str__(self):
        return 'Usuario:\n' + \
            '├─Nombre: ' + self.nombre + \
            '└─Correo: ' + self.correo + '\n'
