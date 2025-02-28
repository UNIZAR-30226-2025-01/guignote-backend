from django.db import models
from usuarios.models import Usuario


class Partida(models.Model):
    jugador_1 = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="partidas_jugador1")
    jugador_2 = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="partidas_jugador2")
    triunfo_palo = models.CharField(max_length=10, choices=[('oros', 'Oros'), ('copas', 'Copas'), ('espadas', 'Espadas'), ('bastos', 'Bastos')])
    mazo_restante = models.JSONField(default=list)
    cartas_jugador_1 = models.JSONField(default=list)
    cartas_jugador_2 = models.JSONField(default=list)
    cartas_jugadas = models.JSONField(default=list)
    puntos_jugador_1 = models.IntegerField(default=0)
    puntos_jugador_2 = models.IntegerField(default=0)
    turno_actual = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name="turno_actual")
    estado_partida = models.CharField(max_length=15, choices=[('EN_JUEGO', 'En juego'), ('FINALIZADO', 'Finalizado')], default='EN_JUEGO')

    def __str__(self):
        return f"Partida entre {self.jugador_1.nombre} y {self.jugador_2.nombre} ({self.estado_partida})"
