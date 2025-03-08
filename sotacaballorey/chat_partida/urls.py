from django.urls import path
from .tests.views.views_chat_partida import enviar_mensaje_chat, obtener_mensajes_chat

urlpatterns = [
    path('chat/enviar/<int:partida_id>/<str:mensaje>/', enviar_mensaje_chat, name="enviar_mensaje_chat"),
    path('chat/mensajes/<int:partida_id>/', obtener_mensajes_chat, name="obtener_mensajes_chat"),
]

