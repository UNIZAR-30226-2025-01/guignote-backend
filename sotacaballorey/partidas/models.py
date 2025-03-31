from django.db import models
from usuarios.models import Usuario
from chat_partida.models import Chat_partida


class Partida(models.Model):
    chat = models.OneToOneField(Chat_partida, on_delete=models.CASCADE, related_name='chat_partida', null=True, blank=True)
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
    
    def save(self, *args, **kwargs):
        """
        Override save method to create and associate a chat room when the match is saved.
        """
        # If this is a new match, create a chat room and add participants
        if not self.chat:
            # Create a new chat room for the match
            chat = Chat_partida.objects.create()
            self.chat = chat
            
            # After saving the match, add the players to the chat
            self.chat.add_participant(self.jugador_1)
            self.chat.add_participant(self.jugador_2)
        
        super(Partida, self).save(*args, **kwargs)  # Save the match


        
    def get_chat_id(self):
        """
        Override the method to return the chat ID for this specific match.
        """
        return self.chat.id if self.chat else None
    


class Partida2v2(models.Model):
    chat = models.OneToOneField(Chat_partida, on_delete=models.CASCADE, related_name='chat_partida2v2', null=True, blank=True)
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
    
    def save(self, *args, **kwargs):
        """
        Override save method to create and associate a chat room when the match is saved.
        """
        # If this is a new match, create a chat room and add participants
        if not self.chat:
            # Create a new chat room for the match
            chat = Chat_partida.objects.create()
            self.chat = chat
            
            # After saving the match, add the players to the chat
            self.chat.add_participant(self.equipo_1_jugador_1)
            self.chat.add_participant(self.equipo_1_jugador_2)
            self.chat.add_participant(self.equipo_2_jugador_1)
            self.chat.add_participant(self.equipo_2_jugador_2)
        
        super(Partida2v2, self).save(*args, **kwargs)  # Save the match


        
    def get_chat_id(self):
        """
        Override the method to return the chat ID for this specific match.
        """
        return self.chat.id if self.chat else None
    
    

