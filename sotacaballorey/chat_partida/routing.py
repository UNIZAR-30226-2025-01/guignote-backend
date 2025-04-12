from django.urls import path
from chat_partida.chatConsumer import ChatConsumer

websocket_urlpatterns = [
    path('ws/chat_partida/<int:chat_id>/', ChatConsumer.as_asgi()),
]
