from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async
from django.utils.timezone import now
from .models import Chat, Mensaje
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'

        # Obtengo usuario autenticado desde el middleware
        self.usuario = self.scope.get('usuario', AnonymousUser())
        if isinstance(self.usuario, AnonymousUser):
            await self.close(code=403)
            return

        try:
            chat = await sync_to_async(Chat.objects.get)(id=self.chat_id)

            usuario1_id = await sync_to_async(lambda: chat.usuario1.id)()
            usuario2_id = await sync_to_async(lambda: chat.usuario2.id)()

            if self.usuario.id not in [usuario1_id, usuario2_id]:
                await self.close(code=403)

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()

        except Chat.DoesNotExist:
            await self.close(code=403)

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)


    async def receive(self, text_data):
        data = json.loads(text_data)
        chat = await sync_to_async(Chat.objects.get)(id=self.chat_id)

        usuario1_id = await sync_to_async(lambda: chat.usuario1.id)()
        usuario2_id = await sync_to_async(lambda: chat.usuario2.id)()

        if data['emisor_id'] not in [usuario1_id, usuario2_id]:
            await self.send(text_data=json.dumps({'error': 'No tienes permiso'}))
            return
        
        mensaje = await sync_to_async(Mensaje.objects.create)(
            chat_id=self.chat_id,
            emisor_id=data['emisor_id'],
            contenido=data['contenido'],
            fecha_envio=now()
        )

        emisor_nombre = await sync_to_async(lambda: mensaje.emisor.nombre)()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'emisor': emisor_nombre,
                'contenido': mensaje.contenido,
                'fecha_envio': mensaje.fecha_envio.strftime('%Y-%m-%d %H:%M:%S')
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))