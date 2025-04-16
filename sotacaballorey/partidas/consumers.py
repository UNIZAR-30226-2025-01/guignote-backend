from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from .models import Partida, JugadorPartida
from asgiref.sync import sync_to_async
from usuarios.models import Usuario
from datetime import datetime
import asyncio
import random
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


class PartidaConsumer(AsyncWebsocketConsumer):
    """
    Consumer que maneja la lógica de partidas de guiñote.
    """

    TIEMPO_TURNO = 20

    async def connect(self):
        self.usuario: Usuario = self.scope.get('usuario', None)
        if not self.usuario or isinstance(self.usuario, AnonymousUser):
            await self.close()
            return
        
        # Obtener parámetros
        query_params = self.scope['query_string'].decode()
        import urllib.parse
        params = urllib.parse.parse_qs(query_params)

        solo_amigos_str = params.get('solo_amigos', ['false'])[0]
        solo_amigos = solo_amigos_str.lower() == 'true'

        id_partida_str = params.get('id_partida', [None])[0]
        if id_partida_str:
            self.partida = await self.obtener_partida_por_id(id_partida_str)
            if not self.partida:
                await self.close()
                return
        else:
            capacidad_str: str = params.get('capacidad', [None])[0]
            if capacidad_str not in ['2', '4']:
                await self.close()
                return
            self.partida: Partida = await self.obtener_o_crear_partida(int(capacidad_str), solo_amigos)

        if not self.partida:
            await self.close()
            return
        self.capacidad = self.partida.capacidad

        # Definimos nombre del grupo
        self.room_group_name = f'partida_{self.partida.id}'

        # Entramos al grupo y agregamos al jugador a la partida
        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name)
        
        jugador, created = await self.agregar_jugador()

        if not jugador:
            await self.send_error('No puedes unirte a la partida')
            await self.close()
            return

        await self.accept()

        if jugador:
            jugador.channel_name = self.channel_name
            await self.db_sync_to_async_save(jugador)

        if created:
            await self.send_to_group(MessageTypes.PLAYER_JOINED, data={
                'message': f'{self.usuario.nombre} se ha unido a la partida.',
                'usuario': {
                    'nombre': self.usuario.nombre,
                    'id': self.usuario.id
                },
                'chat_id': await self.obtener_chat_id(),
                'capacidad': self.capacidad,
                'jugadores': await self.contar_jugadores()
            })
        else:
            # Si te reconectas envíamos más información para que frontend
            # pueda reconstruir estado partida
            await self.send_estado_jugadores(MessageTypes.PLAYER_JOINED)

        # Comprobar si se inicia la partida
        await self.comprobar_inicio_partida()
    
    #------------------------------------------------------------------------------------

    async def disconnect(self, code):
        if hasattr(self, 'partida') and self.partida and self.usuario:
            jugador: JugadorPartida = await self.get_jugador()
            if jugador:
                if self.partida.estado == 'jugando':
                    # Si la partida está en estado 'jugando' desconectamos
                    # al usuario, pero no lo echamos de la partida
                    jugador.conectado = False
                    await self.db_sync_to_async_save(jugador)

                else:
                    # Si aún no ha empezado ('esperando') lo podemos echar
                    # de la partida
                    await self.db_sync_to_async_delete(jugador)
                    count_jugadores = await self.contar_jugadores()
                    if count_jugadores == 0:
                        await self.db_sync_to_async_delete(self.partida)
        
        await self.send_to_group(MessageTypes.PLAYER_LEFT, data={
            'message': f'{self.usuario.nombre} se ha desconectado.',
            'usuario': {
                'nombre': self.usuario.nombre,
                'id': self.usuario.id
            },
            'capacidad': self.capacidad,
            'jugadores': await self.contar_jugadores()
        })

        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name)

    #-----------------------------------------------------------------------------------#
    # Recepción de mensajes del front-end / jugadores                                   #
    #-----------------------------------------------------------------------------------#
    
    async def receive(self, text_data=None, bytes_data=None):
        """
        Recibir y gestionar mensaje de los miembros del grupo
        """
        if not text_data:
            return
        data = json.loads(text_data)
        accion = data.get('accion')
        self.partida = await self.refresh(self.partida)
        if accion == 'jugar_carta':
            carta: dict = data.get('carta')
            await self.jugar_carta(carta)

    #-----------------------------------------------------------------------------------#
    # Métodos para enviar mensajes al front-end                                         #
    #-----------------------------------------------------------------------------------#

    async def send_error(self, mensaje: str):
        """Envía al jugador actual (self) un mensaje de error"""
        await self.send(text_data=json.dumps({
            'type': MessageTypes.ERROR,
            'data': { 'message': mensaje } 
        }))

    async def send_to_group(self, msg_type: str, data):
        """Envía un mensaje con msg_type a todos en el grupo"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_message',
                'msg_type': msg_type,
                'data': data
            }
        )

    #-----------------------------------------------------------------------------------#
    # Lógica de inicio de partida                                                       #
    #-----------------------------------------------------------------------------------#

    async def comprobar_inicio_partida(self):
        """
        Comprueba si se puede iniciar la partida (la sala está llena y la partida
        todavía no ha sido iniciada). Si es posible, inicia turno
        """
        count_jugadores: int = await self.contar_jugadores()
        if count_jugadores == self.capacidad and self.partida.estado == 'esperando':
            
            # Cambiar estado a 'jugando'
            self.partida.estado = 'jugando'
            await self.db_sync_to_async_save(self.partida)

            # Barajar y repartir
            await self.iniciar_partida()

            # Enviar que la partida ha iniciado y estado (cartas, equipos...)
            await self.send_estado_jugadores(MessageTypes.START_GAME)

            # Iniciar el primer turno
            await self.iniciar_siguiente_turno()

    async def iniciar_partida(self):
        """
        Baraja y reparte, define el palo que será el triunfo y
        guarda el estado_json de la partida
        """

        # Crear baraja, barajar y definir palo que será el triunfo
        baraja = self.crear_baraja()
        random.shuffle(baraja)
        
        carta_triunfo = baraja.pop()
        palo_triunfo: str = carta_triunfo['palo']

        # Repartir cartas
        num_cartas: int = 6
        jugadores = await self.get_jugadores()
        for jugador in jugadores:
            mano: list = []
            for _ in range(num_cartas):
                if baraja:
                    mano.append(baraja.pop())
            
            jugador.cartas_json = mano
            await self.db_sync_to_async_save(jugador)

        # Guardar info en estado_json
        estado_json = {
            'baraja': baraja,                   # Cartas restantes
            'triunfo': palo_triunfo,            # Triunfo
            'carta_triunfo': carta_triunfo,     # Carta triunfo
            'fase_arrastre': False,             # Fase arrastre?
            'turno_indice': 0,                  # Índice de jugador que empieza
            'baza_actual': [],                  # Cartas jugadas en la baza actual
            'ultimo_ganador': None              # Quién ganó la última baza
        }
        self.partida.estado_json = estado_json
        await self.db_sync_to_async_save(self.partida)

    def crear_baraja(self):
        """Crea baraja española de 40 cartas"""
        palos = ['oros', 'copas', 'espadas', 'bastos']
        valores = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]
        return [{'palo': p, 'valor': v} for p in palos for v in valores]
            
    #-----------------------------------------------------------------------------------#
    # Lógica de turnos                                                                  #
    #-----------------------------------------------------------------------------------#

    async def iniciar_siguiente_turno(self):
        """Lógica para gestionar el turno del siguiente jugador"""
        estado_json = self.partida.estado_json
        turno_indice: int = estado_json['turno_indice']

        # Si en ultimo_ganador hay algo, ese jugador inicia la siguiente baza
        if estado_json.get('ultimo_ganador') is not None:
            ultimo_ganador_id = estado_json['ultimo_ganador']
            turno_indice = await self.index_de_jugador(ultimo_ganador_id)
            estado_json['turno_indice'] = turno_indice
            self.partida.estado_json = estado_json
            await self.db_sync_to_async_save(self.partida)

        jugadores = await self.get_jugadores()
        orden_jugadores = sorted(jugadores, key=lambda x: x.id)
        if turno_indice >= len(orden_jugadores):
            turno_indice = 0
        jugador_turno: JugadorPartida = orden_jugadores[turno_indice]

        usuario = await sync_to_async(lambda: jugador_turno.usuario)()
        await self.send_to_group(MessageTypes.TURN_UPDATE, {
            'message': f'Es el turno de {usuario.nombre}.',
            'jugador': {
                'nombre': usuario.nombre,
                'id': usuario.id
            },
            'turno_index': turno_indice
        })

        asyncio.create_task(self.temporizador_turno(jugador_turno, turno_indice))
 
    async def temporizador_turno(self, jugador_turno: JugadorPartida, turno_indice: int):
        """
        Espera hasta que el jugador juegue (o acabe el tiempo de turno)
        Si expira el tiempo, juega carta válida aleatoria
        """
        inicio = datetime.now()
        while(datetime.now() - inicio).total_seconds() < self.TIEMPO_TURNO:
            await asyncio.sleep(1)
            self.partida = await self.refresh(self.partida)
            current_turno_index = self.partida.estado_json.get('turno_indice', 0)
            if current_turno_index != turno_indice:
                # Significa que el turno avanzó, así que ya jugó.
                return 
        await self.jugar_carta_automatica(jugador_turno)

    async def jugar_carta_automatica(self, jugador: JugadorPartida):
        """
        Si el tiempo del turno del jugador expirá, forzamos jugada válida
        aleatoria
        """
        estado_json = self.partida.estado_json

        jugador: JugadorPartida = await self.refresh(jugador)
        mano = jugador.cartas_json

        # Filtrar las cartas que son válidas
        cartas_validas = self.obtener_cartas_validas(estado_json, mano, jugador)
        if not cartas_validas:
            carta_a_jugar = mano[0]
        else:
            carta_a_jugar = random.choice(cartas_validas)
        
        await self.procesar_jugada(jugador, carta_a_jugar, automatica=True)

    async def jugar_carta(self, carta):
        """LLamado cuando el jugador envía una carta manualmente"""
        estado_json = self.partida.estado_json
        turno_indice = estado_json['turno_indice']

        jugadores = await self.get_jugadores()
        orden_jugadores = sorted(jugadores, key=lambda x: x.id)
        if turno_indice >= len(orden_jugadores):
            turno_indice = 0

        jugador_turno: JugadorPartida = orden_jugadores[turno_indice]
        jugador_que_juega = await self.get_jugador()

        # ¿Es tu turno?
        if jugador_turno.id != jugador_que_juega.id:
            await self.send_error("No es tu turno")
            return
        
        # ¿Tienes la carta?
        if carta not in jugador_que_juega.cartas_json:
            await self.send_error("No tiene esa carta en tu mano")
            return
        
        # ¿La carta cumple con las reglas del guiñote?
        cartas_validas = self.obtener_cartas_validas(
            estado_json, jugador_que_juega.cartas_json, jugador_que_juega)
        if carta not in cartas_validas:
            await self.send_error("Carta inválida para la fase actual")
            return
        
        await self.procesar_jugada(jugador_que_juega, carta)

    async def procesar_jugada(self, jugador: JugadorPartida, carta, automatica=False):
        """
        Extrae la carta de la mano del jugador, la añade a la baza actual y
        si la baza está completa, decide quién gana
        """
        jugador.cartas_json.remove(carta)
        await self.db_sync_to_async_save(jugador)

        usuario: Usuario = await sync_to_async(lambda: jugador.usuario)()
        await self.send_to_group(MessageTypes.CARD_PLAYER, data={
            'jugador': {
                'nombre': usuario.nombre,
                'id': usuario.id
            },
            'automatica': automatica,
            'carta': carta
        })

        # Añadir carta a baza actual
        estado_json= self.partida.estado_json
        baza_actual = estado_json.get('baza_actual', [])
        baza_actual.append({
            'jugador_id': jugador.id,
            'carta': carta
        })
        estado_json['baza_actual'] = baza_actual
        self.partida.estado_json = estado_json
        await self.db_sync_to_async_save(self.partida)

        # Ver si todos los jugadores han jugado carta en la baza
        if len(baza_actual) == self.capacidad:
            # Calcular ganador de la baza y actualizar puntos
            ganador_id, puntos_baza = self.calcular_ganador(estado_json, baza_actual)
            estado_json['ultimo_ganador'] = ganador_id
            ganador = await self.get_jugador_by_id(ganador_id)
            if ganador.equipo == 1:
                self.partida.puntos_equipo_1 += puntos_baza
            else:
                self.partida.puntos_equipo_2 += puntos_baza

            # Vaciar la baza actual
            estado_json['baza_actual'] = []
            self.partida.estado_json = estado_json
            await self.db_sync_to_async_save(self.partida)

            usuario_ganador: Usuario = await sync_to_async(lambda: ganador.usuario)()
            await self.send_to_group(MessageTypes.ROUND_RESULT, data={
                'ganador': {
                    'nombre': usuario_ganador.nombre,
                    'id': usuario_ganador.id,
                    'equipo': ganador.equipo
                },
                'puntos_baza': puntos_baza,
                'puntos_equipo_1': self.partida.puntos_equipo_1,
                'puntos_equipo_2': self.partida.puntos_equipo_2
            })

            # Robar carta si no estamos en fase de arrastre
            await self.robar_cartas()

            # Comprobar si estamos en fase de arrastre o fin de partida
            await self.verificar_fase_arrastre()
            if await self.comprobar_fin_partida():
                return
            
            estado_json['turno_indice'] = await self.index_de_jugador(ganador_id)
            self.partida.estado_json = estado_json
            await self.db_sync_to_async_save(self.partida)

            # Siguiente turno
            await self.iniciar_siguiente_turno()
        else:
            estado_json['turno_indice'] = (estado_json['turno_indice'] + 1) % self.capacidad
            self.partida.estado_json = estado_json
            await self.db_sync_to_async_save(self.partida)
            await self.iniciar_siguiente_turno()

    def obtener_cartas_validas(self, estado_json, mano, jugador):
        """
        Determina qué cartas de la mano son válidas según el estado del
        juego o si se está en arrastre o no
        """
        # Si no estamos en arrastre, cualquier carta es válida
        if not estado_json.get('fase_arrastre'):
            return mano
        
        # Si la baza está vacía, puedes tirar lo que quieras
        baza = estado_json.get('baza_actual', [])
        if not baza:
            return mano
        
        # En arrastre se debe tirar una carta del mismo palo que la carta
        # inicial de la baza, en su defecto una carta del palo de triunfo o
        # en su defecto cualquier otra carta

        palo_inicial = baza[0]['carta']['palo']
        palo_triunfo = estado_json['triunfo']

        cartas_mismo_palo = [c for c in mano if c['palo'] == palo_inicial]
        if cartas_mismo_palo:
            return cartas_mismo_palo
        
        cartas_triunfo = [c for c in mano if c['palo'] == palo_triunfo]
        if cartas_triunfo:
            return cartas_triunfo
        
        return mano

    def calcular_ganador(self, estado_json, baza_actual):
        """Devuelve (id_del_ganador, puntos_de_la_baza)"""
        palo_inicial = baza_actual[0]['carta']['palo']
        palo_triunfo = estado_json['triunfo']

        puntos_totales = 0
        for jugada in baza_actual:
            puntos_totales += self.valor_carta(jugada['carta'])

        # Identificamos triunfos y no triunfos
        mejor_jugada = None
        for jugada in baza_actual:
            if mejor_jugada is None:
                mejor_jugada = jugada
            else:
                mejor_jugada = self.comparar_cartas(
                    mejor_jugada, jugada, palo_inicial, palo_triunfo)

        return (mejor_jugada['jugador_id'], puntos_totales)
    
    def comparar_cartas(self, jugada_actual, jugada_nueva, palo_inicial, palo_triunfo):
        """Compara las cartas de dos jugadas y devuelve la ganadora"""
        c_ganadora = jugada_actual['carta']
        c_nueva = jugada_nueva['carta']

        es_triunfo_nueva = (c_nueva['palo'] == palo_triunfo)
        es_triunfo_ganadora = (c_ganadora['palo'] == palo_triunfo)
        if es_triunfo_ganadora and not es_triunfo_nueva:
            return jugada_actual
        
        if es_triunfo_nueva and not es_triunfo_ganadora:
            return jugada_nueva
        
        if es_triunfo_ganadora and es_triunfo_nueva:
            if self.valor_carta(c_nueva) > self.valor_carta(c_ganadora) or \
                (self.valor_carta(c_nueva) == self.valor_carta(c_ganadora) and 
                 c_nueva['valor'] > c_ganadora['valor']):
                return jugada_nueva
            else:
                return jugada_actual
            
        mismo_palo_ganadora = (c_ganadora["palo"] == palo_inicial)
        mismo_palo_nueva = (c_nueva["palo"] == palo_inicial)

        if mismo_palo_ganadora and not mismo_palo_nueva:
            return jugada_actual
        
        if mismo_palo_nueva and not mismo_palo_ganadora:
            return jugada_nueva
        
        if mismo_palo_ganadora and mismo_palo_nueva:
            if self.valor_carta(c_nueva) > self.valor_carta(c_ganadora) or \
                (self.valor_carta(c_nueva) == self.valor_carta(c_ganadora) and 
                 c_nueva['valor'] > c_ganadora['valor']):
                return jugada_nueva
            else:
                return jugada_actual
            
        return jugada_actual
        
    def valor_carta(self, carta) -> int:
        """Puntos que aporta cada carta"""
        valor = carta['valor']
        if valor == 1:
            return 11
        if valor == 3:
            return 10
        if valor == 12:
            return 4
        if valor == 11:
            return 3
        if valor == 10:
            return 2
        return 0

    #-----------------------------------------------------------------------------------#
    # Robar cartas y fase de arrastre                                                   #
    #-----------------------------------------------------------------------------------#

    async def robar_cartas(self):
        """
        Cada jugador roba una carta si hay mazo disponible y no 
        estamos en fase de arrastre
        """
        estado_json = self.partida.estado_json
        if not estado_json['fase_arrastre']:
            baraja = estado_json.get('baraja', [])
            if not baraja:
                return
            
            # Orden de robo
            ganador_id = estado_json.get("ultimo_ganador")
            jugadores = await self.get_jugadores()
            orden_jugadores = sorted(jugadores, key=lambda x: x.id)
            idx_ganador = await self.index_de_jugador(ganador_id)
            orden_jugadores = orden_jugadores[idx_ganador:] + orden_jugadores[:idx_ganador]

            for jp in orden_jugadores:
                if baraja:
                    carta = baraja.pop()
                    jp.cartas_json.append(carta)
                    await self.db_sync_to_async_save(jp)

                    if jp.channel_name:
                        await self.channel_layer.send(jp.channel_name, {
                            'type': 'private_message',
                            'msg_type': MessageTypes.CARD_DRAWN,
                            'data': {
                                'carta': carta
                            }
                        })

            estado_json['baraja'] = baraja
            self.partida.estado_json = estado_json
            await self.db_sync_to_async_save(self.partida)

    async def verificar_fase_arrastre(self):
        """Activa fase de arrastre si no quedan cartas en el mazo central"""
        estado_json = self.partida.estado_json
        if not estado_json.get("baraja"):
            estado_json["fase_arrastre"] = True
            self.partida.estado_json = estado_json
            await self.db_sync_to_async_save(self.partida)

            await self.send_to_group(MessageTypes.PHASE_UPDATE, data={
                'message': 'La partida entra en fase de arrastre.'
            })

    #-----------------------------------------------------------------------------------#
    # Fin partida                                                                       #
    #-----------------------------------------------------------------------------------#
    async def comprobar_fin_partida(self):
        """
        Verifica si un equipo supero los 100 puntos, o si no quedan
        cartas en el mazo central ni en las manos de los jugadores
        """
        if self.partida.puntos_equipo_1 >= 100 or self.partida.puntos_equipo_2 >= 100:
            await self.finalizar_partida()
            return True
        
        estado_json = self.partida.estado_json
        if not estado_json.get("baraja"):
            jugadores = await self.get_jugadores()
            manos_vacias = all(len(jp.cartas_json) == 0 for jp in jugadores)
            if manos_vacias:
                await self.finalizar_partida()
                return True
            
        return False
    
    async def finalizar_partida(self):
        """
        Marca la partida como terminada
        """

        e1 = self.partida.puntos_equipo_1
        e2 = self.partida.puntos_equipo_2

        if e1 > e2:
            ganador = 1
        elif e2 > e1:
            ganador = 2
        else:
            ganador = 0

        await self.send_to_group(MessageTypes.GAME_OVER, {
            'message': "Fin de la partida.",
            'ganador_equipo': ganador,
            'puntos_equipo_1': e1,
            'puntos_equipo_2': e2,
        })

        await self.db_sync_to_async_delete(self.partida)

    #-----------------------------------------------------------------------------------#
    # Métodos auxiliares                                                                #
    #-----------------------------------------------------------------------------------#

    async def send_estado_jugadores(self, msg_type: str):
        estado_json = self.partida.estado_json
        mazo = estado_json.get('baraja', [])
        fase_arrastre = estado_json.get('fase_arrastre', False)
        carta_triunfo = estado_json.get('carta_triunfo')
        jugadores = await self.get_jugadores()

        players_info = []
        for jp in jugadores:
            u = await sync_to_async(lambda: jp.usuario)()
            players_info.append({
                'id': u.id,
                'nombre': u.nombre,
                'equipo': jp.equipo,
                'num_cartas': len(jp.cartas_json)
            })

        for jp in jugadores:
            data_para_jugador = {
                'jugadores': players_info,
                'mazo_restante': len(mazo),
                'fase_arrastre': fase_arrastre,
                'mis_cartas': jp.cartas_json,
                'carta_triunfo': carta_triunfo,
                'chat_id': await self.obtener_chat_id()
            }
            if jp.channel_name:
                await self.channel_layer.send(jp.channel_name, {
                    'type': 'private_message',
                    'msg_type': msg_type,
                    'data': data_para_jugador
                })

    async def broadcast_message(self, event):
        msg_type = event['msg_type']
        data = event.get('data', {})
        await self.send(text_data=json.dumps({
            "type": msg_type,
            "data": data
        }))

    async def private_message(self, event):
        msg_type = event.get('msg_type')
        data = event.get('data', {})
        await self.send(text_data=json.dumps({
            "type": msg_type,
            "data": data
        }))

    @database_sync_to_async
    def obtener_o_crear_partida(self, capacidad: int, solo_amigos: bool = False):
        """
        Obtiene una partida disponible (no llena) de capacidad
        dada. Si no existe, la crea.
        """
        partidas_disponibles: Partida = Partida.objects.filter(
            estado='esperando', capacidad=capacidad, solo_amigos=solo_amigos
        )
        for partida in partidas_disponibles:
            if not solo_amigos or self.tiene_amigos_en_partida(partida, self.usuario):
                return partida
        return Partida.objects.create(capacidad=capacidad, solo_amigos=solo_amigos)
    
    @database_sync_to_async
    def obtener_partida_por_id(self, id_partida: str):
        """Obtiene una partida dado su id"""
        try:
            return Partida.objects.get(id=id_partida)
        except Partida.DoesNotExist:
            return None

    @database_sync_to_async
    def agregar_jugador(self):
        """Agrega el usuario a la partida"""
        jugadores_existentes = JugadorPartida.objects.filter(partida=self.partida)

        # Validar amisma si es una partida entre amigos
        if self.partida.solo_amigos and not self.tiene_amigos_en_partida(self.partida, self.usuario):
            return None, False

        count = jugadores_existentes.count()
        equipo = (count % 2) + 1

        jugador, created = JugadorPartida.objects.get_or_create(
            partida=self.partida,
            usuario=self.usuario,
            defaults={'equipo': equipo, 'conectado': True}
        )
        if not created:
            jugador.conectado = True
            jugador.save()
        return (jugador, created)
    
    @database_sync_to_async
    def get_jugador(self):
        """Devuelve el jugador correspondiente al usuario asociado al consumidor"""
        try:
            return JugadorPartida.objects.get(partida=self.partida, usuario=self.usuario)
        except JugadorPartida.DoesNotExist:
            return None
        
    @database_sync_to_async
    def get_jugadores(self):
        """Devuelve los jugadores de la partida"""
        return list(JugadorPartida.objects.filter(
            partida=self.partida).order_by('id'))
    
    @database_sync_to_async
    def contar_jugadores(self):
        """Devuelve el número de jugadores en la partida"""
        return JugadorPartida.objects.filter(partida=self.partida).count()
    
    @database_sync_to_async
    def tiene_amigos_en_partida(self, partida: Partida, usuario: Usuario) -> bool:
        """
        Verifica si el usuario tiene al menos un amigo en la partida dada.
        También devuelve True si la partida está vacía (para permitir crearla).
        """
        jugadores_ids = JugadorPartida.objects.filter(partida=partida).values_list('usuario_id', flat=True)
        amigos_ids = usuario.amigos.values_list('id', flat=True)
        return any(j in amigos_ids for j in jugadores_ids) or not jugadores_ids

    @database_sync_to_async
    def get_jugador_by_id(self, jp_id):
        """Devuelve un jugado dado su id"""
        try:
            return JugadorPartida.objects.get(id=jp_id)
        except JugadorPartida.DoesNotExist:
            return None

    @database_sync_to_async
    def obtener_chat_id(self):
        """Devuelve el chat asociado a la partida"""
        return self.partida.get_chat_id()

    @database_sync_to_async
    def db_sync_to_async_save(self, instance):
        """Modificar instancia de la base de datos"""
        instance.save()

    @database_sync_to_async
    def db_sync_to_async_delete(self, instance):
        """Eliminar instancia de la base de datos"""
        instance.delete()

    @database_sync_to_async
    def refresh(self, jp):
        """Refrescar instancia de la fase de datos"""
        jp.refresh_from_db()
        return jp
    
    async def index_de_jugador(self, jp_id):
        """
        Retorna el índice de un jugador en la lista ordenada de jugadores, para
        sincronizar con turno_index.
        """
        jugadores = await self.get_jugadores()
        orden = sorted(jugadores, key=lambda x: x.id)
        for i, jug in enumerate(orden):
            if jug.id == jp_id:
                return i
        return 0