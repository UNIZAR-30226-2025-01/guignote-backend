from django.urls import path
from .views import views_chat_partida

app_name = "chat_partida"

urlpatterns = [
    path('enviar/<int:partida_id>/<str:mensaje>/', views_chat_partida.enviar_mensaje_chat, name="enviar_mensaje_chat"),
    path('mensajes/<int:partida_id>/', views_chat_partida.obtener_mensajes_chat, name="obtener_mensajes_chat"),
]
