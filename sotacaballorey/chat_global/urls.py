from django.urls import path
from .views import enviar_mensaje, obtener_mensajes

urlpatterns = [
    path('enviar/', enviar_mensaje, name='enviar'),
    path('obtener/', obtener_mensajes, name='obtener')
]
