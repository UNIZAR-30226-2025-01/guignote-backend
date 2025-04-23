from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from partidas.models import Partida, JugadorPartida
from asgiref.sync import sync_to_async
from usuarios.models import Usuario
from datetime import datetime
from .messages import *
from .utils import *
import asyncio
import random
import json

class PartidaConsumer(AsyncWebsocketConsumer):
    """
    Consumer que maneja la lógica de partidas de guiñote.
    """

    TIEMPO_TURNO = 60 # en segundos
    timer_task = None

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
            self.partida = await obtener_partida_por_id(id_partida_str)
            if not self.partida:
                await self.close()
                return
        else:
            capacidad_str: str = params.get('capacidad', [None])[0]
            if capacidad_str not in ['2', '4']:
                await self.close()
                return
            self.partida: Partida = await obtener_o_crear_partida(self.usuario, int(capacidad_str), solo_amigos)

        if not self.partida:
            await self.close()
            return
        self.capacidad = self.partida.capacidad

        # Definimos nombre del grupo
        self.room_group_name = f'partida_{self.partida.id}'

        # Entramos al grupo y agregamos al jugador a la partida
        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name)
        
        jugador, created = await agregar_jugador(self.partida, self.usuario)

        if not jugador:
            await send_error(self.send, 'No puedes unirte a la partida')
            await self.close()
            return

        await self.accept()

        if jugador:
            jugador.channel_name = self.channel_name
            await db_sync_to_async_save(jugador)

        if created:
            await send_to_group(self.channel_layer, self.room_group_name, MessageTypes.PLAYER_JOINED, data={
                'message': f'{self.usuario.nombre} se ha unido a la partida.',
                'usuario': {
                    'nombre': self.usuario.nombre,
                    'id': self.usuario.id
                },
                'chat_id': await obtener_chat_id(self.partida),
                'capacidad': self.capacidad,
                'jugadores': await contar_jugadores(self.partida)
            })
        else:
            # Si te reconectas envíamos más información para que frontend
            # pueda reconstruir estado partida
            await send_estado_jugadores(self, MessageTypes.START_GAME, solo_jugador=jugador)

        # Comprobar si se inicia la partida
        await self.comprobar_inicio_partida()
    
    #------------------------------------------------------------------------------------

    async def disconnect(self, code):
        if hasattr(self, 'partida') and self.partida and self.usuario:
            jugador: JugadorPartida = await get_jugador(self.partida, self.usuario)
            if jugador:
                if self.partida.estado == 'jugando':
                    # Si la partida está en estado 'jugando' desconectamos
                    # al usuario, pero no lo echamos de la partida
                    jugador.conectado = False
                    await db_sync_to_async_save(jugador)

                else:
                    # Si aún no ha empezado ('esperando') lo podemos echar
                    # de la partida
                    await db_sync_to_async_delete(jugador)
                    count_jugadores = await contar_jugadores(self.partida)
                    if count_jugadores == 0:
                        await db_sync_to_async_delete(self.partida)
        
        await send_to_group(self.channel_layer, self.room_group_name, MessageTypes.PLAYER_LEFT, data={
            'message': f'{self.usuario.nombre} se ha desconectado.',
            'usuario': {
                'nombre': self.usuario.nombre,
                'id': self.usuario.id
            },
            'capacidad': self.capacidad,
            'jugadores': await contar_jugadores(self.partida)
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
        self.partida = await refresh(self.partida)
        if accion == 'jugar_carta':
            carta: dict = data.get('carta')
            await self.jugar_carta(carta)

    #-----------------------------------------------------------------------------------#
    # Lógica de inicio de partida                                                       #
    #-----------------------------------------------------------------------------------#

    async def comprobar_inicio_partida(self):
        """
        Comprueba si se puede iniciar la partida (la sala está llena y la partida
        todavía no ha sido iniciada). Si es posible, inicia turno
        """
        count_jugadores: int = await contar_jugadores(self.partida)
        if count_jugadores == self.capacidad and self.partida.estado == 'esperando':
            
            # Cambiar estado a 'jugando'
            self.partida.estado = 'jugando'
            await db_sync_to_async_save(self.partida)

            # Barajar y repartir
            await self.iniciar_partida()

            # Enviar que la partida ha iniciado y estado (cartas, equipos...)
            await send_estado_jugadores(self, MessageTypes.START_GAME)

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
        
        carta_triunfo = baraja[0]
        palo_triunfo: str = carta_triunfo['palo']

        # Repartir cartas
        num_cartas: int = 6
        jugadores = await get_jugadores(self.partida)
        for jugador in jugadores:
            mano: list = []
            for _ in range(num_cartas):
                if baraja:
                    mano.append(baraja.pop())
            
            jugador.cartas_json = mano
            await db_sync_to_async_save(jugador)

        # Guardar info en estado_json
        self.partida.estado_json = {
            'baraja': baraja,                   # Cartas restantes
            'triunfo': palo_triunfo,            # Triunfo
            'carta_triunfo': carta_triunfo,     # Carta triunfo
            'fase_arrastre': False,             # Fase arrastre?
            'baza_actual': [],                  # Cartas jugadas en la baza actual
            'ultimo_ganador': None,             # Quién ganó la última baza
            'turno_actual_id': jugadores[0].id  # Primer jugador en orden por ID
        }
        await db_sync_to_async_save(self.partida)

    def crear_baraja(self):
        """Crea baraja española de 40 cartas"""
        palos = ['Oros', 'Copas', 'Espadas', 'Bastos']
        valores = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]
        return [{'palo': p, 'valor': v} for p in palos for v in valores]
            
    #-----------------------------------------------------------------------------------#
    # Lógica de turnos                                                                  #
    #-----------------------------------------------------------------------------------#

    async def iniciar_siguiente_turno(self):
        """Lógica para gestionar el turno del siguiente jugador"""
        turno_id = self.partida.estado_json['turno_actual_id']
        jugador_turno: JugadorPartida = await get_jugador_by_id(turno_id)

        usuario: Usuario = await sync_to_async(lambda: jugador_turno.usuario)()
        await send_to_group(self.channel_layer, self.room_group_name, MessageTypes.TURN_UPDATE, {
            'message': f'Es el turno de {usuario.nombre}.',
            'jugador': {
                'nombre': usuario.nombre,
                'id': usuario.id
            }
        })

        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()

        self.timer_task = asyncio.create_task(self.temporizador_turno(jugador_turno))

    async def temporizador_turno(self, jugador_turno: JugadorPartida):
        """
        Espera hasta que el jugador juegue (o acabe el tiempo de turno)
        Si expira el tiempo, juega carta válida aleatoria
        """
        inicio = datetime.now()
        while(datetime.now() - inicio).total_seconds() < self.TIEMPO_TURNO:
            await asyncio.sleep(1)
            self.partida = await refresh(self.partida)
            if self.partida.estado_json['turno_actual_id'] != jugador_turno.id:
                return
        await self.jugar_carta_automatica(jugador_turno)

    async def jugar_carta_automatica(self, jugador: JugadorPartida):
        """
        Si el tiempo del turno del jugador expirá, forzamos jugada válida
        aleatoria
        """
        self.partida = await refresh(self.partida)
        estado_json = self.partida.estado_json

        jugador: JugadorPartida = await refresh(jugador)
        mano = jugador.cartas_json

        # Filtrar las cartas que son válidas
        cartas_validas = self.obtener_cartas_validas(estado_json, mano, jugador)
        carta_a_jugar = random.choice(cartas_validas) if cartas_validas else mano[0]
        await self.procesar_jugada(jugador, carta_a_jugar, automatica=True)

    async def jugar_carta(self, carta):
        """LLamado cuando el jugador envía una carta manualmente"""
        estado_json = self.partida.estado_json
        turno_actual_id = estado_json.get('turno_actual_id')

        jugador_que_juega: JugadorPartida = await get_jugador(self.partida, self.usuario)

        # ¿Es tu turno?
        if turno_actual_id != jugador_que_juega.id:
            await send_error(self.send, "No es tu turno")
            return
        
        # ¿Tienes la carta?
        def cartas_son_iguales(c1, c2):
            return c1.get('palo') == c2.get('palo') and int(c1.get('valor')) == int(c2.get('valor'))

        if not any(cartas_son_iguales(carta, c) for c in jugador_que_juega.cartas_json):
            await send_error(self.send, "No tiene esa carta en tu mano")
            return
        
        # ¿La carta cumple con las reglas del guiñote?
        cartas_validas = self.obtener_cartas_validas(
            estado_json, jugador_que_juega.cartas_json, jugador_que_juega)
        if carta not in cartas_validas:
            await send_error(self.send, "Carta inválida para la fase actual")
            return
        
        await self.procesar_jugada(jugador_que_juega, carta)

    async def procesar_jugada(self, jugador: JugadorPartida, carta, automatica=False):
        """
        Extrae la carta de la mano del jugador, la añade a la baza actual y
        si la baza está completa, decide quién gana
        """
        jugador.cartas_json.remove(carta)
        await db_sync_to_async_save(jugador)

        usuario: Usuario = await sync_to_async(lambda: jugador.usuario)()
        await send_to_group(self.channel_layer, self.room_group_name, MessageTypes.CARD_PLAYER, data={
            'jugador': {
                'nombre': usuario.nombre,
                'id': usuario.id
            },
            'automatica': automatica,
            'carta': carta
        })

        # Añadir carta a baza actual
        estado_json = self.partida.estado_json
        baza_actual = estado_json.get('baza_actual', [])
        baza_actual.append({
            'jugador_id': jugador.id,
            'carta': carta
        })
        estado_json['baza_actual'] = baza_actual
        self.partida.estado_json = estado_json
        await db_sync_to_async_save(self.partida)

        if len(baza_actual) == self.capacidad:
            # Fin de la baza: Calcular ganador de la baza
            ganador_id, puntos = self.calcular_ganador(estado_json, baza_actual)
            estado_json['ultimo_ganador'] = ganador_id
            estado_json['baza_actual'] = []

            # Actualizar puntuación
            ganador = await get_jugador_by_id(ganador_id)
            if ganador.equipo == 1:
                self.partida.puntos_equipo_1 += puntos
            else:
                self.partida.puntos_equipo_2 += puntos

            # En la siguiente baza empezará el ganador
            estado_json['turno_actual_id'] = ganador_id
            self.partida.estado_json = estado_json
            await db_sync_to_async_save(self.partida)

            usuario_ganador: Usuario = await sync_to_async(lambda: ganador.usuario)()
            await send_to_group(self.channel_layer, self.room_group_name, MessageTypes.ROUND_RESULT, data={
                'ganador': {
                    'nombre': usuario_ganador.nombre,
                    'id': usuario_ganador.id,
                    'equipo': ganador.equipo
                },
                'puntos_baza': puntos,
                'puntos_equipo_1': self.partida.puntos_equipo_1,
                'puntos_equipo_2': self.partida.puntos_equipo_2
            })

            # Al final de la baza, todos roban una carta
            await self.robar_cartas()

            # Verificar arrastre o fin de partida
            await self.verificar_fase_arrastre()
            if await self.comprobar_fin_partida():
                return

            await self.iniciar_siguiente_turno()
        else:
            # Pasar turno al siguiente jugador
            jugadores = await get_jugadores(self.partida)
            orden = sorted(jugadores, key=lambda x: x.id)
            ids = [j.id for j in orden]
            actual_idx = ids.index(jugador.id)
            siguiente_id = ids[(actual_idx + 1) % self.capacidad]
            estado_json['turno_actual_id'] = siguiente_id
            self.partida.estado_json = estado_json
            await db_sync_to_async_save(self.partida)

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
        """Compara dos jugadas y devuelve la ganadora según las reglas del guiñote"""
        c_ganadora = jugada_actual['carta']
        c_nueva = jugada_nueva['carta']

        # Prioridad palo de triunfo
        if c_ganadora['palo'] == palo_triunfo and c_nueva['palo'] != palo_triunfo:
            return jugada_actual
        elif c_nueva['palo'] == palo_triunfo:
            return jugada_nueva
        
        # Prioridad palo inicial de la baza
        if c_ganadora['palo'] == palo_inicial and c_nueva['palo'] != palo_inicial:
            return jugada_actual
        elif c_nueva['palo'] == palo_inicial:
            return jugada_nueva
        
        # Comparación entre cartas del mismo palo
        fuerza_ganadora = self.fuerza_carta(c_ganadora['valor'])
        fuerza_nueva = self.fuerza_carta(c_nueva['valor'])
        return jugada_nueva if fuerza_nueva < fuerza_ganadora else jugada_actual
        
    def puntos_carta(self, valor: int) -> int:
        """Puntos que aporta una carta según su valor."""
        return {1: 11, 3: 10, 12: 4, 10: 3, 11: 2}.get(valor, 0)

    def fuerza_carta(self, valor: int) -> int:
        """Fuerza relativa de una carta para decidir quién gana la baza."""
        orden = [1, 3, 12, 10, 11, 7, 6, 5, 4, 2]
        return orden.index(valor) if valor in orden else len(orden)

    def valor_carta(self, carta) -> int:
        """Devuelve el valor de la carta"""
        return self.puntos_carta(carta['valor'])

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
            jugadores = await get_jugadores(self.partida)
            orden_jugadores = sorted(jugadores, key=lambda x: x.id)
            idx_ganador = await index_de_jugador(self.partida, ganador_id)
            orden_jugadores = orden_jugadores[idx_ganador:] + orden_jugadores[:idx_ganador]

            for jp in orden_jugadores:
                if baraja:
                    carta = baraja.pop()
                    jp.cartas_json.append(carta)
                    await db_sync_to_async_save(jp)

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
            await db_sync_to_async_save(self.partida)

    async def verificar_fase_arrastre(self):
        """Activa fase de arrastre si no quedan cartas en el mazo central y asigna la carta de triunfo al perdedor"""
        estado_json = self.partida.estado_json
        baraja = estado_json.get('baraja', [])

        if len(baraja) == 1:
            baraja.pop()
            estado_json['baraja'] = baraja
            # Asignar la carta de triunfo al equipo que perdió la última baza antes de arrastre
            carta_triunfo = estado_json.get('carta_triunfo')
            if carta_triunfo:
                ultimo_ganador_id = estado_json.get('ultimo_ganador')
                jugadores = await get_jugadores(self.partida)
                ganador = next((j for j in jugadores if j.id == ultimo_ganador_id), None)
                if ganador:
                    equipo_perdedor = 2 if ganador.equipo == 1 else 1
                    puntos = self.valor_carta(carta_triunfo)
                    if equipo_perdedor == 1:
                        self.partida.puntos_equipo_1 += puntos
                    else:
                        self.partida.puntos_equipo_2 += puntos
                    await db_sync_to_async_save(self.partida)

            estado_json['fase_arrastre'] = True
            self.partida.estado_json = estado_json
            await db_sync_to_async_save(self.partida)

            await send_to_group(self.channel_layer, self.room_group_name, MessageTypes.PHASE_UPDATE, data={
                'message': 'La partida entra en fase de arrastre.',
                'carta_triunfo': carta_triunfo,
                'equipo_que_gana_triunfo': equipo_perdedor
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
            jugadores = await get_jugadores(self.partida)
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

        await send_to_group(self.channel_layer, self.room_group_name, MessageTypes.GAME_OVER, {
            'message': "Fin de la partida.",
            'ganador_equipo': ganador,
            'puntos_equipo_1': e1,
            'puntos_equipo_2': e2,
        })

        await db_sync_to_async_delete(self.partida)

    #-----------------------------------------------------------------------------------#
    # Métodos auxiliares                                                                #
    #-----------------------------------------------------------------------------------#

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