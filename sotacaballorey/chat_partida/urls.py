from django.urls import path
from .views import views_chat_partida

app_name = "chat_partida"

urlpatterns = [
    #1v1
    path('obtener/', views_chat_partida.obtener_mensajes, name='obtener_mensaje_Partida'),
    path('enviar/', views_chat_partida.enviar_mensaje, name='enviar_mensaje_Partida'),
]
