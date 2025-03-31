import json
from django.contrib.auth.models import AnonymousUser
from channels.generic.websocket import AsyncWebsocketConsumer
from chat_partida.models import MensajePartida, Chat_partida as Chat
from partidas.models import Partida, Partida2v2
from usuarios.models import Usuario
from asgiref.sync import sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Called when the WebSocket is handshaking as part of the connection process.
        """
        # Extract match_type and match_id from the URL path
        path = self.scope['path']
        self.usuario = self.scope.get('usuario', AnonymousUser())
        print(self.usuario.nombre)
        path_parts = path.split('/')

        self.match_type = path_parts[2]  # '1v1' or '2v2'
        self.match_id = path_parts[3]   # match_id

        self.room_group_name = f"chat_{self.match_type}_{self.match_id}"

        # Fetch the match instance based on match_type and match_id
        match = await sync_to_async(self.get_match)(self.match_type, self.match_id)

        if match:
            # Get the chat associated with the match
            self.chat = sync_to_async(match.get_chat_id)

            # Ensure the user is part of the match (check chat participants)
            if  await sync_to_async(self.is_user_in_match)(self.usuario, match):
                # Add user to the WebSocket group
                await self.channel_layer.group_add(self.room_group_name, self.channel_name)
                await self.accept()
            else:
                # Reject connection if the user is not part of the match
                await self.send(text_data=json.dumps({"error": "User not in match"}))
                await self.close()
        else:
            # If match is not found
            await self.send(text_data=json.dumps({"error": "Match not found"}))
            await self.close()

    async def disconnect(self, close_code):
        """Called when the WebSocket closes."""
        # Remove user from the WebSocket group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Called when the WebSocket receives a message.
        """
        data = json.loads(text_data)
        message = data.get('message', '').strip()
        user_id = data.get('user_id')

        if message and user_id:
            user = await sync_to_async(self.get_user)(user_id)
            if user:
                # Save the message to the chat
                await sync_to_async(self.save_message)(user, message)
                # Send the message to the WebSocket group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_message",
                        "message": message,
                        "user": user.nombre,
                    }
                )

    async def chat_message(self, event):
        """
        Send the message to the WebSocket.
        """
        message = event['message']
        user = event['user']

        # Send the message to the WebSocket client
        await self.send(text_data=json.dumps({
            'message': message,
            'user': user,
        }))

    def get_match(self, match_type, match_id):
        """Fetch the match instance based on match type ('1v1' or '2v2')."""
        if match_type == '1v1':
            return self.get_partida(match_id)
        elif match_type == '2v2':
            return self.get_partida2v2(match_id)
        return None

    def get_partida(self, match_id):
        """Retrieve a 1v1 match (Partida)."""
        try:
            return Partida.objects.get(id=match_id)
        except Partida.DoesNotExist:
            return None

    def get_partida2v2(self, match_id):
        """Retrieve a 2v2 match (Partida2v2)."""
        try:
            return Partida2v2.objects.get(id=match_id)
        except Partida2v2.DoesNotExist:
            return None

    def get_user(self, user_id):
        """Retrieve the user instance by ID."""
        try:
            return Usuario.objects.get(id=user_id)
        except Usuario.DoesNotExist:
            return None

    def is_user_in_match(self, user, match):
        """Check if the user is part of the match by comparing user ID."""
        if isinstance(match, Partida):  # 1v1 match
            return user.id in [match.jugador_1.id, match.jugador_2.id]
        elif isinstance(match, Partida2v2):  # 2v2 match
            return user.id in [
                match.equipo_1_jugador_1.id, match.equipo_1_jugador_2.id,
                match.equipo_2_jugador_1.id, match.equipo_2_jugador_2.id
            ]
        return False

    def save_message(self, user, message):
        """Save the message to the associated chat."""
        chat = Chat.objects.get(id=self.match_id)
        MensajePartida.objects.create(
            emisor=user,
            contenido=message,
            chat=chat
        )
