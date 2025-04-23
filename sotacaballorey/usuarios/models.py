from django.db import models
from django.core.validators import MinValueValidator
from aspecto_carta.models import CardSkin
from dorso_carta.models import CardBack

class Usuario(models.Model):
    unlocked_skins = models.ManyToManyField(CardSkin, related_name='players', blank=True)
    unlocked_backs = models.ManyToManyField(CardBack, related_name='players', blank=True)
    nombre = models.CharField\
        (max_length=64,  blank=False, null=False, unique=True)
    correo = models.EmailField\
        (max_length=320, blank=False, null=False, unique=True)
    contrasegna = models.CharField\
        (max_length=128, blank=False, null=False, unique=False)
    amigos = models.ManyToManyField\
        ('self', symmetrical=True, blank=True)
    imagen = models.ImageField\
        (upload_to='imagenes_perfil/', blank=True, null=True)

    # Puntuaciones
    victorias = models.IntegerField\
        (null=False, default=0, validators=[MinValueValidator(0)])
    derrotas = models.IntegerField\
        (null=False, default=0, validators=[MinValueValidator(0)])
    racha_victorias = models.IntegerField\
        (null=False, default=0, validators=[MinValueValidator(0)])
    mayor_racha_victorias = models.IntegerField\
        (null=False, default=0, validators=[MinValueValidator(0)])
    elo = models.IntegerField(default=1200, validators=[MinValueValidator(0)])
    elo_parejas = models.IntegerField(default=1200, validators=[MinValueValidator(0)])
    
    def __str__(self):
        return 'Usuario:\n' + \
            '├─Nombre: ' + self.nombre + '\n' + \
            '└─Correo: ' + self.correo + '\n'

class SolicitudAmistad(models.Model):
    emisor = models.ForeignKey\
        (Usuario, on_delete=models.CASCADE, blank=False, unique=False, null=False,
         related_name='solicitudes_enviadas')
    receptor = models.ForeignKey\
        (Usuario, on_delete=models.CASCADE, blank=False, unique=False, null=False,
         related_name='solicitudes_recibidas')
    
    class Meta:
        unique_together = ('emisor', 'receptor')


    def __str__(self):
        return 'Solicitud de amistad:\n' + \
            '├─Emisor  : ' + self.emisor.nombre + '\n' + \
            '└─Receptor: ' + self.receptor.nombre + '\n'