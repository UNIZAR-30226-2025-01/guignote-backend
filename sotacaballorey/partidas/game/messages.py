from asgiref.sync import sync_to_async
from .utils import *
import json

class MessageTypes:
    START_GAME = 'start_game'
    GAME_OVER = 'end_game'
    PLAYER_JOINED = 'player_joined'
    PLAYER_LEFT = 'player_left'
    TURN_UPDATE = 'turn_update'
    CARD_PLAYER = 'card_played'
    ROUND_RESULT = 'round_result'
    PHASE_UPDATE = 'phase_update'
    CARD_DRAWN = 'card_drawn'
    ERROR = "error"
    CANTO = "canto"
    CAMBIO_SIETE = "cambio_siete"

#-----------------------------------------------------------------------------------#
# Métodos para enviar mensajes al front-end                                         #
#-----------------------------------------------------------------------------------#

async def send_error(send, mensaje: str):
    """Envía al jugador actual (self) un mensaje de error"""
    await send(text_data=json.dumps({
        'type': MessageTypes.ERROR,
        'data': { 'message': mensaje } 
    }))

async def send_to_group(channel_layer, room_group_name, msg_type: str, data):
    """Envía un mensaje con msg_type a todos en el grupo"""
    await channel_layer.group_send(
        room_group_name,
        {
            'type': 'broadcast_message',
            'msg_type': msg_type,
            'data': data
        }
    )

async def send_estado_jugadores(self, msg_type: str, solo_jugador: JugadorPartida = None):
    estado_json = self.partida.estado_json
    mazo = estado_json.get('baraja', [])
    fase_arrastre = estado_json.get('fase_arrastre', False)
    carta_triunfo = estado_json.get('carta_triunfo')
    jugadores = [solo_jugador] if solo_jugador else await get_jugadores(self.partida)

    players_info = []
    for jp in jugadores:
        u = await sync_to_async(lambda: jp.usuario)()
        players_info.append({
            'id': u.id,
            'nombre': u.nombre,
            'equipo': jp.equipo,
            'num_cartas': len(jp.cartas_json)
        })

    chat_id = await obtener_chat_id(self.partida)

    for jp in jugadores:
        data_para_jugador = {
            'jugadores': players_info,
            'mazo_restante': len(mazo),
            'fase_arrastre': fase_arrastre,
            'mis_cartas': jp.cartas_json,
            'carta_triunfo': carta_triunfo,
            'chat_id': chat_id
        }
        if jp.channel_name:
            await self.channel_layer.send(jp.channel_name, {
                'type': 'private_message',
                'msg_type': msg_type,
                'data': data_para_jugador
            })