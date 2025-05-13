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
    PAUSE = "pause"
    ALL_PAUSE = "all_pause"
    RESUME = "resume"
    DEBUG_STATE = "debug_state"
    SCORE_UPDATE = "score_update"

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
    todos_jugadores = await get_jugadores(self.partida)

    baza_actual = estado_json.get('baza_actual', [])
    cartas_jugadas = {b['jugador_id']: b['carta'] for b in baza_actual}

    turno_id = self.partida.estado_json['turno_actual_id']
    jugador_turno: JugadorPartida = await get_jugador_by_id(turno_id)
    usuario: Usuario = await sync_to_async(lambda: jugador_turno.usuario)()

    players_info = []
    for jp in todos_jugadores:
        u = await sync_to_async(lambda: jp.usuario)()
        carta_jugada = cartas_jugadas.get(jp.id, None)
        players_info.append({
            'id': u.id,
            'nombre': u.nombre,
            'equipo': jp.equipo,
            'num_cartas': len(jp.cartas_json),
            'carta_jugada': carta_jugada
        })

    chat_id = await obtener_chat_id(self.partida)

    jugadores_a_enviar = [solo_jugador] if solo_jugador else todos_jugadores
    for jp in jugadores_a_enviar:
        data_para_jugador = {
            'jugadores': players_info,
            'mazo_restante': len(mazo),
            'fase_arrastre': fase_arrastre,
            'mis_cartas': jp.cartas_json,
            'carta_triunfo': carta_triunfo,
            'chat_id': chat_id,
            'tiempo_turno': self.partida.tiempo_turno,
            'puntos_equipo_1': self.partida.puntos_equipo_1,
            'puntos_equipo_2': self.partida.puntos_equipo_2,
            'pausados': len(self.partida.jugadores_pausa or []),
            'turno': usuario.id,
        }
        if jp.channel_name:
            await self.channel_layer.send(jp.channel_name, {
                'type': 'private_message',
                'msg_type': msg_type,
                'data': data_para_jugador
            })

async def send_debug_state(consumer, estado_json):
    """Envía el estado actual de la partida para debugging"""
    await consumer.send(text_data=json.dumps({
        'type': MessageTypes.DEBUG_STATE,
        'data': estado_json
    }))