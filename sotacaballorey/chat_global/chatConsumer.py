from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Chat, Mensaje, obtener_o_crear_chat
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async
from django.utils.timezone import now
from usuarios.models import Usuario
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.receptor_id = self.scope['url_route']['kwargs']['receptor_id']

        # Obtengo usuario autenticado desde el middleware
        self.usuario = self.scope.get('usuario', AnonymousUser())
        if isinstance(self.usuario, AnonymousUser):
            await self.close(code=403)
            return

        try:
            self.receptor = await sync_to_async(Usuario.objects.get)(id=self.receptor_id)
            
            self.chat = await sync_to_async(obtener_o_crear_chat)(self.usuario, self.receptor)
            if not self.chat:
                await self.close(code=403)
                return
            
            self.chat_id = self.chat.id
            self.room_group_name = f'chat_{self.chat_id}'

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()

        except Usuario.DoesNotExist:
            await self.close(code=403)

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)


    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            contenido = data.get('contenido', '').strip()

            if not contenido:
                await self.send(text_data=json.dumps({'error': 'El mensaje no puede estar vacío'}))
                return
            
            mensaje = await sync_to_async(Mensaje.objects.create)(
                chat=self.chat,
                emisor=self.usuario,
                contenido=contenido,
                fecha_envio=now()
            )
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'emisor': self.usuario.id,
                    'contenido': mensaje.contenido,
                    'fecha_envio': mensaje.fecha_envio.strftime('%Y-%m-%d %H:%M:%S')
                }
            )
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'error': 'Formato de mensaje inválido'}))
        except Usuario.DoesNotExist:
            await self.send(text_data=json.dumps({'error': 'Receptor no encontrado'}))            

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))