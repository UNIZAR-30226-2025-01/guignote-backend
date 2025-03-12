from django.db import models
from partidas.models import Partida  # Ensure this is correctly imported
from partidas.models import Partida2v2  # Ensure this is correctly imported
from usuarios.models import Usuario  # Ensure this is correctly imported
from django.utils.timezone import now  # To automatically store timestamps

class ChatPartida(models.Model):
    partida = models.ForeignKey(Partida, on_delete=models.CASCADE, related_name="mensajes")
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="mensajes_enviados")
    mensaje = models.TextField()
    timestamp = models.DateTimeField(default=now)  # Stores date & hour automatically

    class Meta:
        ordering = ["timestamp"]  # Messages are retrieved in chronological order

    def __str__(self):
        return f"Chat in {self.partida} - {self.usuario.nombre}: {self.mensaje[:30]}..."
    
class ChatPartidaParejas(models.Model):
    partida = models.ForeignKey(Partida2v2, on_delete=models.CASCADE, related_name="mensajes_parejas")
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="mensajes_parejas_enviados")
    mensaje = models.TextField()
    timestamp = models.DateTimeField(default=now)  # Stores date & hour automatically

    class Meta:
        ordering = ["timestamp"]  # Messages are retrieved in chronological order

    def __str__(self):
        return f"Chat in {self.partida} - {self.usuario.nombre}: {self.mensaje[:30]}..."

