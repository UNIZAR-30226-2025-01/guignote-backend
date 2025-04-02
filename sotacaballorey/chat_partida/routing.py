from django.urls import path
from chat_partida.chatConsumer import ChatConsumer

app_name = 'chat_partida'

websocket_urlpatterns_partida = [
    # WebSocket URL for 1v1 matches (Partida)
    path('ws/chat/1v1/<int:match_id>/', ChatConsumer.as_asgi(), name='chat_websocket_1v1'),

    # WebSocket URL for 2v2 matches (Partida2v2)
    path('ws/chat/2v2/<int:match_id>/', ChatConsumer.as_asgi(), name='chat_websocket_2v2'),
]
