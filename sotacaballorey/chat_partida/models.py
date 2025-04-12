from django.db import models
from usuarios.models import Usuario
from django.utils.timezone import now

class Chat_partida(models.Model):
    """
    Chat model representing a chat room for a match.
    """
    
    # Many-to-many relationship with users (participants in the chat)
    participants = models.ManyToManyField(Usuario, related_name="chat_participations")
    
    def add_participant(self, user) -> bool:
        """
        Add a participant to the chat.
        """
        from partidas.models import JugadorPartida
        try:
            partida: Partida = self.chat_partida
            if not JugadorPartida.objects.filter(partida=partida, usuario=user).exists():
                return False
            self.participants.add(user)
            return True
        except Partida.DoesNotExist:
            return False

    def remove_participant(self, user):
        """
        Remove a participant from the chat.
        """
        from partidas.models import JugadorPartida
        try:
            partida: Partida = self.chat_partida
            if not JugadorPartida.objects.filter(partida=partida, usuario=user).exists():
                return False
            self.participants.remove(user)
        except Partida.DoesNotExist:
            return False

    def get_participants(self):
        """
        Get a list of participants in the chat.
        """
        return self.participants.all()
    

        
class MensajePartida(models.Model):
    """
    Model for a message associated with a match chat.
    """
    emisor = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='mensajes_enviados_partida'
    )
    contenido = models.TextField(blank=False, null=False)
    fecha_envio = models.DateTimeField(default=now)
    
    # ForeignKey to Chat instead of using ContentType for generic relation
    chat = models.ForeignKey(Chat_partida, on_delete=models.CASCADE, related_name='mensajes_partida')
    
    class Meta:
        indexes = [
            models.Index(fields=["chat"]),
        ]
        
        # Order messages by their sending date
        ordering = ['fecha_envio']

    def __str__(self):
        return f'Mensaje de {self.emisor.nombre} en chat {self.chat.id}'
    
