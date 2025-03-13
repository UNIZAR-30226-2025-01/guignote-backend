from .chatConsumer import ChatConsumer
from django.urls import path

websocket_urlpatterns = [
    path('ws/chat/<int:receptor_id>/', ChatConsumer.as_asgi()),
]