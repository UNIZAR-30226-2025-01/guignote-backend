from django.db import models
from django.core.validators import MinValueValidator
from aspecto_carta.models import CardSkin
from dorso_carta.models import CardBack
from tapete.models import Tapete

class Usuario(models.Model):
    ELO_RANKS = [
        ('guiri', 'Guiri'),
        ('casual', 'Casual'),
        ('parroquiano', 'Parroquiano'),
        ('octogenario', 'Octogenario'),
        ('leyenda', 'Leyenda del Imserso')
    ]

    unlocked_skins = models.ManyToManyField(CardSkin, related_name='players', blank=True)
    unlocked_backs = models.ManyToManyField(CardBack, related_name='players', blank=True)
    unlocked_tapetes = models.ManyToManyField(Tapete, related_name='players', blank=True)
    
    equipped_skin = models.ForeignKey(CardSkin, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipped_by')
    equipped_back = models.ForeignKey(CardBack, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipped_by')
    equipped_tapete = models.ForeignKey(Tapete, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipped_by')
    
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
    elo_rank = models.CharField(max_length=20, choices=ELO_RANKS, default='casual')
    
    def save(self, *args, **kwargs):
        # Update ELO rank based on current ELO
        is_new = self.pk is None  # Check if this is a new user instance
        if is_new:
            super().save(*args, **kwargs)  # Save the user to get an ID
            self.save()
            return

        if self.elo >= 2700:
            self.elo_rank = 'leyenda'
        elif self.elo >= 2100:
            self.elo_rank = 'octogenario'
        elif self.elo >= 1600:
            self.elo_rank = 'parroquiano'
        elif self.elo >= 1200:
            self.elo_rank = 'casual'
        else:
            self.elo_rank = 'guiri'
        
         # Unlock Default Skin and Tapete for all users
        # Ensure the default skin and tapete are only added if they are not already unlocked
        default_skin = CardSkin.objects.get(name="Default")  # Ensure this skin exists
        default_tapete = Tapete.objects.get(name="Default")  # Ensure this tapete exists

        # Only add if not already unlocked
        if default_skin not in self.unlocked_skins.all():
            self.unlocked_skins.add(default_skin)

        if default_tapete not in self.unlocked_tapetes.all():
            self.unlocked_tapetes.add(default_tapete)


        # Unlock Poker Skin for "Parroquiano"
        if self.elo_rank == 'casual' or self.elo_rank == 'parroquiano' or self.elo_rank == 'octogenario' or self.elo_rank == 'leyenda':
            red_black_tapete = Tapete.objects.get(name="Rojo-negro")  # Ensure this skin exists
            if red_black_tapete not in self.unlocked_tapetes.all():
                self.unlocked_tapetes.add(red_black_tapete)

        if self.elo_rank == 'parroquiano' or self.elo_rank == 'octogenario' or self.elo_rank == 'leyenda':
            poker_skin = CardSkin.objects.get(name="Poker")  # Ensure this skin exists
            if poker_skin not in self.unlocked_skins.all():
                self.unlocked_skins.add(poker_skin)

        if self.elo_rank == 'octogenario' or self.elo_rank == 'leyenda':
            blue_silver_tapete = Tapete.objects.get(name="Azul-plata")  # Ensure this skin exists
            if blue_silver_tapete not in self.unlocked_tapetes.all():
                self.unlocked_tapetes.add(blue_silver_tapete)

        # Unlock Paint Skin for "Leyenda"
        if self.elo_rank == 'leyenda':
            paint_skin = CardSkin.objects.get(name="Paint")  # Ensure this skin exists
            if paint_skin not in self.unlocked_skins.all():
                self.unlocked_skins.add(paint_skin)

            red_gold_tapete = Tapete.objects.get(name="Rojo-dorado")  # Ensure this skin exists
            if red_gold_tapete not in self.unlocked_tapetes.all():
                self.unlocked_tapetes.add(red_gold_tapete)

        # Save the updated user
        super().save(*args, **kwargs)

        
    
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