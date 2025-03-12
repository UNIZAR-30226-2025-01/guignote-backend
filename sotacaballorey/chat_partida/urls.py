from django.urls import path
from .views import views_chat_partida, views_chat_partida_parejas

app_name = "chat_partida"

urlpatterns = [
    #1v1
    path('enviar/<int:partida_id>/<str:mensaje>/', views_chat_partida.enviar_mensaje_chat, name="enviar_mensaje_chat"),
    path('mensajes/<int:partida_id>/', views_chat_partida.obtener_mensajes_chat, name="obtener_mensajes_chat"),
    
    #2v2
    path('2v2/enviar/<int:partida_id>/<str:mensaje>/', views_chat_partida_parejas.enviar_mensaje_chat, name="enviar_mensaje_chat_parejas"),
    path('2v2/mensajes/<int:partida_id>/', views_chat_partida_parejas.obtener_mensajes_chat, name="obtener_mensajes_chat_parejas"),
]
