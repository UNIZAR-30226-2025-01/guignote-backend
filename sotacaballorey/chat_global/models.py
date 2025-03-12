from django.utils.timezone import now
from usuarios.models import Usuario
from django.db import models

class Chat(models.Model):
    usuario1 = models.ForeignKey\
        (Usuario, on_delete=models.CASCADE, related_name='chats_usuario1')
    usuario2 = models.ForeignKey\
        (Usuario, on_delete=models.CASCADE, related_name='chats_usuario2')
    
    class Meta:
        # Evito chats duplicados
        unique_together = ('usuario1', 'usuario2')

    def __str__(self):
        return f'Chat entre {self.usuario1.nombre} y {self.usuario2.nombre}'
    
class Mensaje(models.Model):
    chat = models.ForeignKey\
        (Chat, on_delete=models.CASCADE, related_name='mensajes_glob')
    emisor = models.ForeignKey\
        (Usuario, on_delete=models.CASCADE, related_name='mensajes_enviados_glob')
    contenido = models.TextField\
        (blank = False, null = False)
    fecha_envio = models.DateTimeField(default=now)

    class Meta:
        # Ordenar mensajes por fecha
        ordering = ['fecha_envio']

    def __str__(self):
        return f'Mensaje de {self.emisor.nombre} en chat {self.chat.id}'


def obtener_o_crear_chat(usuario1, usuario2):
    """
    Devuelve el chat entre dos usuarios. Si no existe, lo crea
    """
    
    # Solo se permiten chats entre amigos
    if not usuario1.amigos.filter(id=usuario2.id).exists():
        return None
    
    chat, creado = Chat.objects.get_or_create(
        usuario1 = min(usuario1, usuario2, key=lambda u: u.id),
        usuario2 = max(usuario1, usuario2, key=lambda u: u.id)
    )
    return chat
