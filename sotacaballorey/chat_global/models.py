from django.db import models
from django.utils.timezone import now
from usuarios.models import Usuario

class ChatGlobal(models.Model):
    emisor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="emisor_global")
    receptor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="receptor_global")
    timestamp = models.DateTimeField(default=now)
    mensaje = models.TextField()

    def __str__(self):
        return f"{self.sender.nombre} → {self.recipient.nombre}: {self.mensaje[:30]}"  # Show preview
