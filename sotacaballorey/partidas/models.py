from django.db import models
from usuarios.models import Usuario


class Partida(models.Model):
    jugador_1 = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="partidas_jugador1")
    jugador_2 = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="partidas_jugador2")
    triunfo_palo = models.CharField(max_length=10, choices=[('oros', 'Oros'), ('copas', 'Copas'), ('espadas', 'Espadas'), ('bastos', 'Bastos')])
    ganador = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name="partidas_ganadas")
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

class Partida2v2(models.Model):
    equipo_1_jugador_1 = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="partidas_equipo1_jugador1")
    equipo_1_jugador_2 = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="partidas_equipo1_jugador2")
    equipo_2_jugador_1 = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="partidas_equipo2_jugador1")
    equipo_2_jugador_2 = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="partidas_equipo2_jugador2")

    triunfo_palo = models.CharField(
        max_length=10,
        choices=[('oros', 'Oros'), ('copas', 'Copas'), ('espadas', 'Espadas'), ('bastos', 'Bastos')]
    )

    # Winning team reference
    equipo_ganador = models.IntegerField(
        choices=[(1, "Equipo 1"), (2, "Equipo 2")], 
        null=True, blank=True
    )

    mazo_restante = models.JSONField(default=list)
    cartas_equipo_1_jugador_1 = models.JSONField(default=list)
    cartas_equipo_1_jugador_2 = models.JSONField(default=list)
    cartas_equipo_2_jugador_1 = models.JSONField(default=list)
    cartas_equipo_2_jugador_2 = models.JSONField(default=list)
    cartas_jugadas = models.JSONField(default=list)

    puntos_equipo_1 = models.IntegerField(default=0)
    puntos_equipo_2 = models.IntegerField(default=0)

    turno_actual = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name="turno_actual_2v2")

    estado_partida = models.CharField(
        max_length=15, 
        choices=[('EN_JUEGO', 'En juego'), ('FINALIZADO', 'Finalizado')], 
        default='EN_JUEGO'
    )

    def __str__(self):
        return f"Partida 2v2 - {self.equipo_1_jugador_1.nombre} & {self.equipo_1_jugador_2.nombre} vs {self.equipo_2_jugador_1.nombre} & {self.equipo_2_jugador_2.nombre} ({self.estado_partida})"
