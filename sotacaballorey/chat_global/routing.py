from .chatConsumer import ChatConsumer
from django.urls import path

websocket_urlpatterns = [
    path('ws/chat/<int:chat_id>/', ChatConsumer.as_asgi()),
]