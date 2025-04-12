import json
from django.contrib.auth.models import AnonymousUser
from channels.generic.websocket import AsyncWebsocketConsumer
from chat_partida.models import MensajePartida, Chat_partida as Chat
from usuarios.models import Usuario
from asgiref.sync import sync_to_async
from django.utils.timezone import now

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Called when the WebSocket is handshaking as part of the connection process.
        """
        self.usuario = self.scope.get('usuario', AnonymousUser())
        self.chat_id = self.scope['url_route']['kwargs'].get('chat_id')

        if not self.chat_id or isinstance(self.usuario, AnonymousUser):
            await self.close(code=403)
            return

        # Cargar el chat
        self.chat = await sync_to_async(self.get_chat)()
        if not self.chat:
            await self.send(text_data=json.dumps({'error': 'Chat no encontrado'}))
            await self.close(code=404)
            return

        ok = await sync_to_async(self.chat.add_participant)(self.usuario)
        if not ok:
            await self.send(text_data=json.dumps({'error': 'No puedes unirte a este chat'}))
            await self.close(code=403)
            return

        self.room_group_name = f'chat_{self.chat_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """Called when the WebSocket closes."""
        # Remove user from the WebSocket group
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            await sync_to_async(self.chat.remove_participant)(self.usuario)

    async def receive(self, text_data):
        """
        Called when the WebSocket receives a message.
        """
        try:
            data = json.loads(text_data)
            contenido = data.get('contenido', '').strip()

            if not contenido:
                await self.send(text_data=json.dumps({'error': 'El mensaje no puede estar vacío'}))
                return

            mensaje = await sync_to_async(MensajePartida.objects.create)(
                chat=self.chat,
                emisor=self.usuario,
                contenido=contenido,
                fecha_envio=now()
            )

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'emisor': {
                        'id': self.usuario.id,
                        'nombre': self.usuario.nombre
                    },
                    'contenido': mensaje.contenido,
                    'fecha_envio': mensaje.fecha_envio.strftime('%Y-%m-%d %H:%M:%S')
                }
            )
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'error': 'Formato de mensaje inválido'}))
    
    async def chat_message(self, event):
        """
        Send the message to the WebSocket.
        """
        await self.send(text_data=json.dumps(event))

    def get_chat(self):
        try:
            return Chat.objects.get(id=self.chat_id)
        except Chat.DoesNotExist:
            return None 
