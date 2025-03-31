from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from usuarios.models import Usuario  # Ensure this is correctly imported
from django.utils.timezone import now  # To automatically store timestamps

class Chat_partida(models.Model):
    """
    Chat model representing a chat room for a match.
    """
    
    # Many-to-many relationship with users (participants in the chat)
    participants = models.ManyToManyField(Usuario, related_name="chat_participations")
    
    def add_participant(self, user):
        """
        Add a participant to the chat.
        """
        self.participants.add(user)

    def remove_participant(self, user):
        """
        Remove a participant from the chat.
        """
        self.participants.remove(user)

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
    
