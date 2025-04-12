from .consumers import PartidaConsumer
from django.urls import path

websocket_urlpatterns = [
    path('ws/partida/', PartidaConsumer.as_asgi()),
]