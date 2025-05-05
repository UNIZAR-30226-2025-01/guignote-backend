from django.core.validators import MinValueValidator, MaxValueValidator
from chat_partida.models import Chat_partida
from usuarios.models import Usuario
from django.db import models

ESTADOS_PARTIDA = [
    ('esperando', 'Esperando'),
    ('jugando', 'Jugando'),
    ('pausada', 'Pausada'),
    ('terminada', 'Terminada'),
]

class Partida(models.Model):
    """Modelo que representa una partida de guiñote"""
    chat = models.OneToOneField(
        Chat_partida, on_delete=models.CASCADE, related_name='chat_partida', null=True, blank=True
    )
    capacidad = models.IntegerField(
        choices=[(2, 2), (4, 4)], default=2
    )
    estado = models.CharField(
        max_length=9, choices=ESTADOS_PARTIDA, default='esperando'
    )
    puntos_equipo_1 = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    puntos_equipo_2 = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    estado_json = models.JSONField(default=dict, blank=True)
    es_revueltas = models.BooleanField(default=False)
    cantos_realizados = models.JSONField(default=dict)
    jugadores_pausa = models.JSONField(default=list)
    # Campos para personalización de partidas
    solo_amigos = models.BooleanField(default=False)
    tiempo_turno = models.IntegerField(
        choices=[(15, 'Bajo'), (30, 'Normal'), (60, 'Largo')],
        default=30
    )
    permitir_revueltas = models.BooleanField(default=True)
    reglas_arrastre = models.BooleanField(default=True)
    es_personalizada = models.BooleanField(default=False)

    def __str__(self):
        return f'Partida {self.id} - {self.capacidad} jugadores ({self.estado})'
    
    def get_chat_id(self):
        if not self.chat:
            chat = Chat_partida.objects.create()
            self.chat = chat
            self.save()
        return self.chat.id

    def save(self, *args, **kwargs):
        """Sobreescribir <save> para crear chat cuando se cree nueva partida"""
        if not self.pk and not self.chat:
            chat = Chat_partida.objects.create()
            self.chat = chat
        super().save(*args, **kwargs)    

    def delete(self, *args, **kwargs):
        """Sobreescribir <delete> para borrar el chat cuando se termine/elimine la partida"""
        if self.chat:
            self.chat.delete()
        super().delete(*args, **kwargs)

class JugadorPartida(models.Model):
    """Modelo intermedio para relacionar un Usuario con una Partida"""
    partida = models.ForeignKey(
        Partida, on_delete=models.CASCADE, related_name='jugadores'
    )
    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='partidas'
    )
    equipo = models.IntegerField(
        default=1, validators=[MinValueValidator(1), MaxValueValidator(2)]
    )
    cartas_json = models.JSONField(default=list, blank=True)
    conectado = models.BooleanField(default=True)
    channel_name = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return f'Jugador {self.usuario.nombre} en partida {self.partida.id}'