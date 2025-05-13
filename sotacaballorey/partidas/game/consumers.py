from partidas.elo import calcular_nuevo_elo, calcular_nuevo_elo_parejas
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from partidas.models import Partida, JugadorPartida
from asgiref.sync import sync_to_async
from usuarios.models import Usuario
from datetime import datetime
from .messages import *
from .utils import *
import urllib.parse
import asyncio
import random
import json

class PartidaConsumer(AsyncWebsocketConsumer):
    """
    Consumer que maneja la lógica de partidas de guiñote.
    """

    palos = ['Oros', 'Copas', 'Espadas', 'Bastos']
    timer_task = None

    async def connect(self):

        self.usuario: Usuario = self.scope.get('usuario', None)
        if not self.usuario or isinstance(self.usuario, AnonymousUser):
            await self.close()
            return
        
        # Obtener y parsear parámetros de la URL
        query_params = self.scope['query_string'].decode()
        params = urllib.parse.parse_qs(query_params)

        id_partida_str = params.get('id_partida', [None])[0]
        es_personalizada = params.get('es_personalizada', ['false'])[0].lower() == 'true'
        try:
            capacidad_value = params.get('capacidad', 2)
            if isinstance(capacidad_value, list):
                capacidad_value = str(capacidad_value[0])
            else:
                capacidad_value = str(capacidad_value)
            self.capacidad = int(capacidad_value)
            self.capacidad = 2 if self.capacidad not in [2,4] else self.capacidad
        except Exception as e:
            print("Exception caught:", e)
            self.capacidad = 2
        
        # Manejar conexión a partida existente por ID
        if id_partida_str:
            self.partida = await obtener_partida_por_id(id_partida_str)

            if not self.partida:
                await self.close()
                return
            
            if self.partida.capacidad != self.capacidad:
                print(f"Error: La partida solicitada no es del tipo correcto (error de capacidad)")
                await self.close()
                return

            if self.partida.solo_amigos and \
                not await tiene_amigos_en_partida(self.partida, self.usuario):
                    await self.close()
                    return

        # Crear o unise a partida
        else:
            if es_personalizada:
                self.partida = await obtener_o_crear_partida_personalizada(self.usuario, params)
                
                if self.partida.solo_amigos and \
                    not await tiene_amigos_en_partida(self.partida, self.usuario):
                        await self.close()
                        return
            else:
                self.partida = await obtener_o_crear_partida(self.usuario, self.capacidad)

        if not self.partida:
            print(f"error not partida")
            await self.close()
            return

        jugador_existente = await get_jugador(self.partida, self.usuario)
        if jugador_existente:
            if jugador_existente.channel_name:
                # Si el jugador ya está conectado en otro canal, cerramos esa conexión
                await self.channel_layer.send(jugador_existente.channel_name, {
                    'type': 'close_connection'
                })

        # Definimos nombre del grupo
        self.room_group_name = f'partida_{self.partida.id}'

        # Entramos al grupo y agregamos al jugador a la partida
        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name)

        jugador, created = await agregar_jugador(self.partida, self.usuario)

        if not jugador:
            print(f"error not jugador")
            await self.close()
            return

        await self.accept()

        if jugador:
            jugador.channel_name = self.channel_name
            jugador.conectado = True

            try:
                await db_sync_to_async_save(jugador)
            except Exception as e:
                print(f"Error al guardar el jugador: {e}")

            if str(jugador.id) in self.partida.jugadores_pausa:
                self.partida.jugadores_pausa.remove(str(jugador.id))
                await db_sync_to_async_save(self.partida)

            await send_to_group(self.channel_layer, self.room_group_name, MessageTypes.PLAYER_JOINED, data={
                'message': f'{self.usuario.nombre} se ha unido a la partida.',
                'usuario': {
                    'nombre': self.usuario.nombre,
                    'id': self.usuario.id
                },
                'chat_id': await obtener_chat_id(self.partida),
                'partida_id': self.partida.id,
                'capacidad': self.capacidad,
                'jugadores': await contar_jugadores(self.partida),
                'pausados': len(self.partida.jugadores_pausa or [])
            })      

        if self.partida.estado == 'jugando':
            await send_estado_jugadores(self, MessageTypes.START_GAME, solo_jugador=jugador)

        await self.comprobar_inicio_partida()
    
    #------------------------------------------------------------------------------------

    async def disconnect(self, code):
        if hasattr(self, 'partida') and self.partida and self.usuario:
            try:
                self.partida = await refresh(self.partida)
            except Partida.DoesNotExist:
                if hasattr(self, 'room_group_name') and self.channel_name:
                    await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
                return
            jugador: JugadorPartida = await get_jugador(self.partida, self.usuario)
            if jugador:
                if self.partida.estado in ['jugando', 'pausada']:
                    # Si la partida está en curso, marcamos decomo desconectado
                    # pero no lo eliminamos de la partida
                    jugador.conectado = False
                    await db_sync_to_async_save(jugador)


                    if self.partida.estado == 'jugando' and str(jugador.id) not in self.partida.jugadores_pausa:
                        await self.procesar_pausa()
                        await db_sync_to_async_save(self.partida)

                elif self.partida.estado in ['esperando', 'finalizada']:
                    # Si aún no ha empezado ('esperando') lo podemos echar
                    # de la partida. Si todos se desconectan antes de que comienze
                    # la partida, se elimina
                    await db_sync_to_async_delete(jugador)
                    count_jugadores = await contar_jugadores(self.partida)
                    if count_jugadores == 0:
                        await db_sync_to_async_delete(self.partida)
        if hasattr(self, 'room_group_name') and self.usuario:
            await send_to_group(self.channel_layer, self.room_group_name, MessageTypes.PLAYER_LEFT, data={
                'message': f'{self.usuario.nombre} se ha desconectado.',
                'usuario': {
                    'nombre': self.usuario.nombre,
                    'id': self.usuario.id
                },
                'capacidad': self.capacidad,
                'jugadores': await contar_jugadores(self.partida)
            })

            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

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
        elif accion == 'cantar':
            await self.procesar_canto()
        elif accion == 'cambiar_siete':
            await self.procesar_cambio_siete()
        elif accion == 'pausa':
            await self.procesar_pausa()
        elif accion == 'anular_pausa':
            await self.procesar_anular_pausa()
        elif accion == 'debug_state':
            # Get current game state
            jugadores = await sync_to_async(list)(self.partida.jugadores.all())
            jugadores_data = []
            for j in jugadores:
                usuario_id = await sync_to_async(lambda: j.usuario.id)()
                usuario_nombre = await sync_to_async(lambda: j.usuario.nombre)()
                jugadores_data.append({
                    'usuario': {
                        'id': usuario_id,
                        'nombre': usuario_nombre
                    },
                    'equipo': j.equipo,
                    'cartas_json': j.cartas_json
                })
            
            estado = {
                'solo_amigos': self.partida.solo_amigos,
                'capacidad':self.capacidad,
                'partida': self.partida.estado_json,
                'jugadores': jugadores_data,
                'mazo': self.partida.estado_json.get('baraja', []),
                'pozo': self.partida.estado_json.get('baza_actual', []),
                'turno_actual': self.partida.estado_json.get('turno_actual_id'),
                'estado': self.partida.estado,
                'puntos_equipo_1': self.partida.puntos_equipo_1,
                'puntos_equipo_2': self.partida.puntos_equipo_2
            }
            await send_debug_state(self, estado)
        elif accion == 'debug_finalizar':
            # Debug action to trigger finalizar_partida
            await self.finalizar_partida()
        elif accion == 'debug_set_score':
            # Debug action to set scores for both teams
            puntos_equipo1 = data.get('puntos_equipo1', 0)
            puntos_equipo2 = data.get('puntos_equipo2', 0)
            
            self.partida.puntos_equipo_1 = puntos_equipo1
            self.partida.puntos_equipo_2 = puntos_equipo2
            await db_sync_to_async_save(self.partida)
            
            await send_to_group(self.channel_layer, self.room_group_name, MessageTypes.SCORE_UPDATE, data={
                'puntos_equipo_1': puntos_equipo1,
                'puntos_equipo_2': puntos_equipo2
            })

    #-----------------------------------------------------------------------------------#
    # Lógica de inicio de partida                                                       #
    #-----------------------------------------------------------------------------------#

    async def comprobar_inicio_partida(self):
        """
        Comprueba si se puede iniciar la partida (la sala está llena y la partida
        todavía no ha sido iniciada). Si es posible, inicia turno
        """
        count_jugadores: int = await contar_jugadores(self.partida)

        if count_jugadores == self.capacidad:
            if self.partida.estado == 'pausada':
                self.partida.jugadores_pausa = []
            
                # Cambiar estado a 'jugando'
                self.partida.estado = 'jugando'
                await db_sync_to_async_save(self.partida)

                # Enviar estado de la partida a todos
                await send_estado_jugadores(self, MessageTypes.START_GAME)

                # Si estaba en medio de un turno, reanudar
                await self.iniciar_siguiente_turno()
            
            elif self.partida.estado == 'esperando':
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
        valores = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]
        return [{'palo': p, 'valor': v} for p in self.palos for v in valores]
            
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
        while(datetime.now() - inicio).total_seconds() < self.partida.tiempo_turno:
            await asyncio.sleep(1)

            try:
                self.partida = await refresh(self.partida)
            except Partida.DoesNotExist:
                return

            if self.partida.estado != 'jugando':
                return

            estado_json = self.partida.estado_json or {}

            turno_actual_id = estado_json.get('turno_actual_id')
            if turno_actual_id is None or turno_actual_id != jugador_turno.id:
                return
            
        if self.partida.estado == 'jugando':
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
        cartas_validas = await self.obtener_cartas_validas(estado_json, mano, jugador)
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
        cartas_validas = await self.obtener_cartas_validas(
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

            # Las 10 últimas
            jugadores = await get_jugadores(self.partida)
            if not estado_json.get('baraja') and \
                all(len(j.cartas_json) == 0 for j in jugadores):
                    puntos += 10

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

    async def obtener_cartas_validas(self, estado_json, mano, jugador):
        """
        Determina qué cartas de la mano son válidas según el estado del
        juego o si se está en arrastre o no
        """
        # Si no estamos en arrastre, cualquier carta es válida
        if not estado_json.get('fase_arrastre') or not self.partida.reglas_arrastre:
            return mano
        
        # Si la baza está vacía, puedes tirar lo que quieras
        baza = estado_json.get('baza_actual', [])
        if not baza:
            return mano
        
        palo_inicial = baza[0]['carta']['palo']
        palo_triunfo = estado_json['triunfo']

        # Función para ver si una carta gana
        def gana(carta_a, carta_b):
            return self.comparar_cartas({'carta': carta_a}, {'carta': carta_b}, palo_inicial, palo_triunfo)

        # Si mi compañero de equipo va ganando la baza puedo tirar cualquier carta
        if self.capacidad == 4:
            mejor_id = self.calcular_ganador(estado_json, baza)[0]
            mejor_jugador = await get_jugador_by_id(mejor_id)
            if mejor_jugador and mejor_jugador.equipo == jugador.equipo and mejor_jugador.id != jugador.id:
                return mano
                    
        # Cartas del mismo palo
        cartas_mismo_palo = [c for c in mano if c['palo'] == palo_inicial]
        if cartas_mismo_palo:
            mismas_en_baza = [j['carta'] for j in baza if j['carta']['palo'] == palo_inicial]
            if mismas_en_baza:
                mejor_en_baza = max(mismas_en_baza, key=lambda c: self.fuerza_carta(c['valor']))
                ganadoras = [c for c in cartas_mismo_palo if gana(c, mejor_en_baza)]
                return ganadoras if ganadoras else cartas_mismo_palo
            return cartas_mismo_palo

        # No tiene del mismo palo. Buscar triunfos
        cartas_triunfo = [c for c in mano if c['palo'] == palo_triunfo]
        if cartas_triunfo:
            triunfo_en_baza = [j['carta'] for j in baza if j['carta']['palo'] == palo_triunfo]
            if triunfo_en_baza:
                mejor_triunfo_en_baza = max(triunfo_en_baza, key=lambda c: self.fuerza_carta(c['valor']))
                ganadoras = [c for c in cartas_triunfo if gana(c, mejor_triunfo_en_baza)]
                if ganadoras:
                    return ganadoras
            return cartas_triunfo
        
        return mano

    def calcular_ganador(self, estado_json, baza_actual):
        """Devuelve (id_del_ganador, puntos_de_la_baza)"""
        palo_inicial = baza_actual[0]['carta']['palo']
        palo_triunfo = estado_json['triunfo']

        puntos_totales = 0
        for jugada in baza_actual:
            puntos_totales += self.valor_carta(jugada['carta'])

        mejor_jugada = baza_actual[0]
        for jugada in baza_actual[1:]:
            mejor_jugada = self.comparar_cartas(mejor_jugada, jugada, palo_inicial, palo_triunfo)

        return (mejor_jugada['jugador_id'], puntos_totales)
    
    def comparar_cartas(self, jugada_actual, jugada_nueva, palo_inicial, palo_triunfo):
        """Compara dos jugadas y devuelve la ganadora según las reglas del guiñote"""
        c_ganadora = jugada_actual['carta']
        c_nueva = jugada_nueva['carta']

        # Prioridad palo de triunfo
        if c_ganadora['palo'] == palo_triunfo and c_nueva['palo'] != palo_triunfo:
            return jugada_actual
        elif c_nueva['palo'] == palo_triunfo and c_ganadora['palo'] != palo_triunfo:
            return jugada_nueva
        
        # Prioridad palo inicial de la baza
        if c_ganadora['palo'] == palo_inicial and c_nueva['palo'] != palo_inicial:
            return jugada_actual
        elif c_nueva['palo'] == palo_inicial and c_ganadora['palo'] != palo_inicial:
            return jugada_nueva
        
        # Comparación entre cartas del mismo palo
        if c_ganadora['palo'] == c_nueva['palo']:
            fuerza_ganadora = self.fuerza_carta(c_ganadora['valor'])
            fuerza_nueva = self.fuerza_carta(c_nueva['valor'])
            return jugada_nueva if fuerza_nueva > fuerza_ganadora else jugada_actual

        # Si las cartas son de diferente palo, devolvemos la carta que haya ganado
        return jugada_actual
        
    def puntos_carta(self, valor: int) -> int:
        """Puntos que aporta una carta según su valor."""
        return {1: 11, 3: 10, 12: 4, 10: 3, 11: 2}.get(valor, 0)

    def fuerza_carta(self, valor: int) -> int:
        """Fuerza relativa de una carta para decidir quién gana la baza."""
        orden = [1, 3, 12, 10, 11, 7, 6, 5, 4, 2]
        return len(orden) - orden.index(valor) if valor in orden else 0

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
        if not self.partida.reglas_arrastre or self.partida.estado_json['fase_arrastre']:
            return

        estado_json = self.partida.estado_json
        baraja = estado_json.get('baraja', [])

        if len(baraja) == 0:
            estado_json['fase_arrastre'] = True
            self.partida.estado_json = estado_json
            await db_sync_to_async_save(self.partida)

            await send_to_group(self.channel_layer, self.room_group_name, MessageTypes.PHASE_UPDATE, data={
                'message': 'La partida entra en fase de arrastre'
            })

    #-----------------------------------------------------------------------------------#
    # Fin partida                                                                       #
    #-----------------------------------------------------------------------------------#
    async def comprobar_fin_partida(self):
        """
        Verifica las condiciones de fin de partida:
        - Si estamos en revueltas, termina cuando un equipo supera los 100 puntos.
        - Si estamos en partida normal, termina solo cuando se vacían las manos y el mazo,
          y un équipo ha superado los 100 puntos.
        """
        try:
            self.partida = await refresh(self.partida)
        except Partida.DoesNotExist:
            return False
        estado_json = self.partida.estado_json

        if self.partida.es_revueltas:
            if self.partida.puntos_equipo_1 > 100 or self.partida.puntos_equipo_2 > 100:
                await self.finalizar_partida()
                return True
            return False
        
        else:
            if not estado_json.get('baraja'):
                jugadores = await get_jugadores(self.partida)
                manos_vacias = all(len(jp.cartas_json) == 0 for jp in jugadores)
                if manos_vacias:
                    await self.finalizar_partida()
                    return True
            return False
    
    async def finalizar_partida(self):
        """
        Decide el equipo ganador según reglas:
        - En partida normal, si ambos superan 100, gana quien hizo las 10 últimas.
        - En revueltas, gana quien supera primero los 100.
        """
        try:
            self.partida = await refresh(self.partida)
        except Partida.DoesNotExist:
            return

        e1 = self.partida.puntos_equipo_1
        e2 = self.partida.puntos_equipo_2

        if e1 > 100 and e2 > 100 and not self.partida.es_revueltas:
            # Ambos equipos superan 100
            # El que hizo las 10 últimas gana
            ultimo_ganador_id = self.partida.estado_json.get('ultimo_ganador')
            ganador = (await get_jugador_by_id(ultimo_ganador_id)).equipo if ultimo_ganador_id else 0
        elif e1 > 100:
            # Si un equipo supera 100, gana ese equipo
            ganador = 1
        elif e2 > 100:
            # Si un equipo supera 100, gana ese equipo
            ganador = 2
        elif self.partida.permitir_revueltas:
            await self.iniciar_revueltas()
            return
        else:
            ganador = 0

        jugadores = await get_jugadores(self.partida)
        if not self.partida.es_personalizada:
            await actualizar_estadisticas(self.partida, ganador)

            # Get team players
            equipo1 = [j for j in jugadores if j.equipo == 1]
            equipo2 = [j for j in jugadores if j.equipo == 2]
            
            # Update ELOs
            if self.capacidad == 2:
                if not equipo1 or not equipo2:
                    print("Error: Missing team members for 1v1 game")
                    return
                    
                # 1v1 game
                jugador1 = equipo1[0]
                jugador2 = equipo2[0]
                
                # Get current ELOs
                elo1 = await sync_to_async(lambda: jugador1.usuario.elo)()
                elo2 = await sync_to_async(lambda: jugador2.usuario.elo)()
                
                # Calculate new ELOs
                resultado = 1 if ganador == 1 else 0
                nuevo_elo1, nuevo_elo2 = calcular_nuevo_elo(elo1, elo2, resultado)

                # Update ELOs
                await sync_to_async(lambda: setattr(jugador1.usuario, 'elo', nuevo_elo1))()
                await sync_to_async(lambda: setattr(jugador2.usuario, 'elo', nuevo_elo2))()
                await sync_to_async(lambda: jugador1.usuario.save())()
                await sync_to_async(lambda: jugador2.usuario.save())()
                
                # Verify saved ELOs
                saved_elo1 = await sync_to_async(lambda: jugador1.usuario.elo)()
                saved_elo2 = await sync_to_async(lambda: jugador2.usuario.elo)()
                
            else:
                # 2v2 game
                elo_equipo1 = [await sync_to_async(lambda: j.usuario.elo_parejas)() for j in equipo1]
                elo_equipo2 = [await sync_to_async(lambda: j.usuario.elo_parejas)() for j in equipo2]
                
                # Calculate new ELOs
                resultado = 1 if ganador == 1 else 0
                nuevo_elo1 = calcular_nuevo_elo_parejas(elo_equipo1, elo_equipo2, resultado)
                nuevo_elo2 = calcular_nuevo_elo_parejas(elo_equipo2, elo_equipo1, 1 - resultado)
                
                # Update ELOs
                for j, nuevo_elo in zip(equipo1, nuevo_elo1):
                    await sync_to_async(lambda: setattr(j.usuario, 'elo_parejas', nuevo_elo))()
                    await sync_to_async(lambda: j.usuario.save())()
                
                for j, nuevo_elo in zip(equipo2, nuevo_elo2):
                    await sync_to_async(lambda: setattr(j.usuario, 'elo_parejas', nuevo_elo))()
                    await sync_to_async(lambda: j.usuario.save())()

        await send_to_group(self.channel_layer, self.room_group_name, MessageTypes.GAME_OVER, {
            'message': "Fin de la partida.",
            'ganador_equipo': ganador,
            'puntos_equipo_1': e1,
            'puntos_equipo_2': e2,
        })

        for jugador in jugadores:
            if jugador:
                jugador.conectado = False
                await db_sync_to_async_save(jugador)
                if jugador.channel_name:
                    await self.channel_layer.send(jugador.channel_name, {
                        'type': 'close_connection'
                    })

        try:
            await marcar_como_finalizada(self.partida)
        except Partida.DoesNotExist:
            return

    async def iniciar_revueltas(self):
        """Inicia la partida de revueltas"""
        # Guardamos el ganador de la baza final, que será quien tenga el primer turno
        # en revueltas
        ultimo_ganador_id = self.partida.estado_json.get('ultimo_ganador')

        self.partida.es_revueltas = True
        self.partida.cantos_realizados = {}
        await db_sync_to_async_save(self.partida)
        await self.iniciar_partida()

        # Restauramos último ganador
        self.partida.estado_json['turno_actual_id'] = ultimo_ganador_id
        await db_sync_to_async_save(self.partida)

        await send_estado_jugadores(self, MessageTypes.START_GAME)
        await self.iniciar_siguiente_turno()

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

    #-----------------------------------------------------------------------------------#
    # Lógica de cantos                                                                  #
    #-----------------------------------------------------------------------------------#
    
    async def procesar_canto(self):
        """Procesa la acción de cantar de un jugador"""
        jugador: JugadorPartida = await get_jugador(self.partida, self.usuario)

        # Validar que puede cantar
        if not await self.puede_cantar(jugador):
            await send_error(self.send, "No puedes cantar ahora")
            return
        
        # Buscar cantos posibles
        cantos = await self.detectar_cantos(jugador)
        if not cantos:
            await send_error(self.send, "No tienes cartas para cantar")
            return
        
        # Aplicar cantos y sumar puntos
        puntos = 0
        canto_messages = []

        for canto in cantos:
            if canto['tipo'] == '20':
                if canto['palo'] not in self.partida.cantos_realizados.get('20', []):
                    if '20' not in self.partida.cantos_realizados:
                        self.partida.cantos_realizados['20'] = []
                    self.partida.cantos_realizados['20'].append(canto['palo'])
                    puntos += 20
                    canto_messages.append(f"20 ({canto['palo']})")
            elif canto['tipo'] == '40':
                if not self.partida.cantos_realizados.get('40', False):
                    self.partida.cantos_realizados['40'] = True
                    puntos += 40
                    canto_messages.append("40 (triunfo)")

        if puntos == 0:
            await send_error(self.send, "No hay cantos válidos disponibles")
            return
        
        # Sumar puntos al equipo
        if jugador.equipo == 1:
            self.partida.puntos_equipo_1 += puntos
        else:
            self.partida.puntos_equipo_2 += puntos
        await db_sync_to_async_save(self.partida)

        usuario = await sync_to_async(lambda: jugador.usuario)()
        await send_to_group(self.channel_layer, self.room_group_name, MessageTypes.CANTO, {
            'jugador': {
                'id': usuario.id,
                'nombre': usuario.nombre,
                'equipo': jugador.equipo
            },
            'cantos': canto_messages,
            'puntos': puntos,
            'puntos_equipo_1': self.partida.puntos_equipo_1,
            'puntos_equipo_2': self.partida.puntos_equipo_2
        })

    async def puede_cantar(self, jugador: JugadorPartida) -> bool:
        """Determina si el jugador puede cantar"""
        estado_json = self.partida.estado_json
        
        # Solo puede cantar si:
        # 1. Su equipo ganó la última baza
        # 2. No se ha tirado ninguna carta en la baza actual
        ultimo_ganador = await get_jugador_by_id(estado_json.get('ultimo_ganador'))
        
        return (
            ultimo_ganador and
            ultimo_ganador.equipo == jugador.equipo and
            len(estado_json.get('baza_actual', [])) == 0
        )    

    async def detectar_cantos(self, jugador: JugadorPartida) -> list:
        """Detecta qué cantos puede hacer el jugador"""
        cartas = jugador.cartas_json
        palo_triunfo = self.partida.estado_json['triunfo']
        cantos = []

        for palo in self.palos:
            tiene_rey = any(c['palo'] == palo and c['valor'] == 12 for c in cartas)
            tiene_sota = any(c['palo'] == palo and c['valor'] == 10 for c in cartas)
            
            if tiene_rey and tiene_sota:
                if palo == palo_triunfo:
                    cantos.append({'tipo': '40', 'palo': palo})
                else:
                    cantos.append({'tipo': '20', 'palo': palo})
        
        return cantos
    
    #-----------------------------------------------------------------------------------#
    # Cambio del 7                                                                      #
    #-----------------------------------------------------------------------------------#

    async def procesar_cambio_siete(self):
        """Procesar la acción de cambiar el 7 de triunfo"""
        estado_json = self.partida.estado_json
        jugador: JugadorPartida = await get_jugador(self.partida, self.usuario)

        # Validacion
        if not await self.puede_cambiar_siete(jugador):
            await send_error(self.send, 'No puedes cambiar el 7 ahora')
            return
        
        palo_triunfo = estado_json['triunfo']
        siete_triunfo = {'palo': palo_triunfo, 'valor': 7}

        # Comprobar que tiene el 7 de triunfo
        if siete_triunfo not in jugador.cartas_json:
            await send_error(self.send, 'No tienes el 7 de triunfo')
            return

        # Intercambio
        carta_triunfo_actual = estado_json['carta_triunfo']
        jugador.cartas_json.remove(siete_triunfo)  
        jugador.cartas_json.append(carta_triunfo_actual)
        estado_json['carta_triunfo'] = siete_triunfo
        estado_json['baraja'][0] = siete_triunfo
        await db_sync_to_async_save(jugador)
        await db_sync_to_async_save(self.partida)

        usuario = await sync_to_async(lambda: jugador.usuario)()
        await send_to_group(self.channel_layer, self.room_group_name, MessageTypes.CAMBIO_SIETE, {
            'jugador': {
                'id': usuario.id,
                'nombre': usuario.nombre,
                'equipo': jugador.equipo
            },
            'carta_robada': carta_triunfo_actual
        })

    async def puede_cambiar_siete(self, jugador: JugadorPartida) -> bool:
        """Determina si el jugador puede cambiar el 7"""
        estado_json = self.partida.estado_json
        
        # Solo puede cambiar si:
        # 1. Su equipo ganó la última baza
        # 2. No se ha tirado ninguna carta en la baza actual
        # 3. No estamos en fase de arrastre
        ultimo_ganador = await get_jugador_by_id(estado_json.get('ultimo_ganador'))
        
        return (
            not estado_json.get('fase_arrastre', False) and
            ultimo_ganador and
            ultimo_ganador.equipo == jugador.equipo and
            len(estado_json.get('baza_actual', [])) == 0
        )
    
    #-----------------------------------------------------------------------------------#
    # Pausar partida por acuerdo                                                                     #
    #-----------------------------------------------------------------------------------#

    async def procesar_pausa(self):
        """Procesa la solicitud de pausar la partida"""
        if self.partida.estado != 'jugando':
            await send_error(self.send, 'Solo se puede pausar partidas en curso')
            return
        
        jugador = await get_jugador(self.partida, self.usuario)
        if not jugador:
            await send_error(self.send, 'No estás en la partida')
            return
        
        # Añadir a lista de jugadores que han pedido pausa
        if str(jugador.id) not in self.partida.jugadores_pausa:
            self.partida.jugadores_pausa.append(str(jugador.id))
            await db_sync_to_async_save(self.partida)
            
            usuario = await sync_to_async(lambda: jugador.usuario)()
            await send_to_group(self.channel_layer, self.room_group_name, MessageTypes.PAUSE, {
                'jugador': {
                    'id': usuario.id,
                    'nombre': usuario.nombre,
                    'equipo': jugador.equipo
                },
                'num_solicitudes_pausa': len(self.partida.jugadores_pausa) 
            })

        # Si todos han pedido pausa, pausamos la partida
        if len(self.partida.jugadores_pausa) >= self.capacidad or self.partida.solo_amigos:
            await self.pausar_partida()

    async def procesar_anular_pausa(self):
        """Procesa la solicitud de anular una pausa pendiente"""
        if self.partida.estado != 'jugando':
            await send_error(self.send, 'No hay pausa pendiente')
            return
        
        jugador = await get_jugador(self.partida, self.usuario)
        if not jugador:
            await send_error(self.send, 'No estás en esta partida')
            return
        
        # Quitar de la lista de jugadores que han pedido la pausa al jugador
        if str(jugador.id) in self.partida.jugadores_pausa:
            self.partida.jugadores_pausa.remove(str(jugador.id))
            await db_sync_to_async_save(self.partida)

            usuario = await sync_to_async(lambda: jugador.usuario)()
            await send_to_group(self.channel_layer, self.room_group_name, MessageTypes.RESUME, {
                'jugador': {
                    'id': usuario.id,
                    'nombre': usuario.nombre,
                    'equipo': jugador.equipo
                },
                'num_solicitudes_pausa': len(self.partida.jugadores_pausa) 
            })
        
    async def pausar_partida(self):
        """Pausa la partida y desconecta a todos los jugadores"""
        self.partida.estado = 'pausada'
        await db_sync_to_async_save(self.partida)
        
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()

        await send_to_group(self.channel_layer, self.room_group_name, MessageTypes.ALL_PAUSE, {
            'message': 'La partida ha sido pausada por acuerdo de todos los jugadores.'
        })

        # Desconectar a los jugadores
        jugadores = await get_jugadores(self.partida)
        for jugador in jugadores:
            if jugador:
                jugador.conectado = False
                await db_sync_to_async_save(jugador)
                if jugador.channel_name:
                    await self.channel_layer.send(jugador.channel_name, {
                        'type': 'close_connection'
                    })

    async def close_connection(self, event=None):
        """Cierra la conexión del websocket"""
        await self.close()