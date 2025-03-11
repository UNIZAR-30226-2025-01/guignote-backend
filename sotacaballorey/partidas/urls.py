from django.urls import path
from .views import *

urlpatterns = [
    path('crear/', crear_partida, name='crear_partida'),
    path('estado/<int:partida_id>/', obtener_estado_partida, name='obtener_estado_partida'),
    path('alterar/<int:partida_id>/estado/', cambiar_estado_partida, name='cambiar_estado_partida'),
]
