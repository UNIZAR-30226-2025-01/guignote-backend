from partidas.models import Partida, JugadorPartida
from channels.db import database_sync_to_async
from usuarios.models import Usuario

@database_sync_to_async
def obtener_o_crear_partida(usuario: Usuario, capacidad: int):
    """
    Obtiene una partida disponible (no llena) de capacidad
    dada. Si no existe, la crea.
    """
    partidas_disponibles: Partida = Partida.objects.filter(
        estado='esperando', capacidad=capacidad, es_personalizada=False
    ).exclude(jugadores__usuario=usuario)
    if partidas_disponibles:
        return partidas_disponibles[0]
    partida = Partida.objects.create(capacidad=capacidad)
    partida.save()
    return partida

@database_sync_to_async
def obtener_partida_por_id(id_partida: str):
    """Obtiene una partida dado su id"""
    try:
        return Partida.objects.get(id=id_partida)
    except Partida.DoesNotExist:
        return None

@database_sync_to_async
def agregar_jugador(partida: Partida, usuario: Usuario):
    """Agrega el usuario a la partida"""
    jugadores_existentes = JugadorPartida.objects.filter(partida=partida)

    equipo = (jugadores_existentes.count() % 2) + 1
    jugador, created = JugadorPartida.objects.get_or_create(
        partida=partida,
        usuario=usuario,
        defaults={'equipo': equipo}
    )
    jugador.conectado = True
    jugador.save()
    return (jugador, created)

@database_sync_to_async
def get_jugador(partida: Partida, usuario: Usuario):
    """Devuelve el jugador correspondiente al usuario asociado al consumidor"""
    try:
        return JugadorPartida.objects.get(partida=partida, usuario=usuario)
    except JugadorPartida.DoesNotExist:
        return None
    
@database_sync_to_async
def get_jugadores(partida: Partida):
    """Devuelve los jugadores de la partida"""
    return list(JugadorPartida.objects.filter(
        partida=partida).order_by('id'))

@database_sync_to_async
def contar_jugadores(partida: Partida):
    """Devuelve el número de jugadores en la partida"""
    partida.refresh_from_db()
    jugadores = JugadorPartida.objects.filter(partida=partida)
    for jugador in jugadores:
        jugador.refresh_from_db()
    return jugadores.filter(conectado=True).count()

def _tiene_amigos_en_partida(partida: Partida, usuario: Usuario) -> bool:
    """
    Verifica si el usuario tiene al menos un amigo en la partida dada.
    También devuelve True si la partida está vacía (para permitir crearla).
    """
    jugadores_ids = JugadorPartida.objects.filter(partida=partida).values_list('usuario_id', flat=True)
    amigos_ids = usuario.amigos.values_list('id', flat=True)
    return any(j in amigos_ids for j in jugadores_ids) or not jugadores_ids

@database_sync_to_async
def tiene_amigos_en_partida(partida: Partida, usuario: Usuario) -> bool:
    return _tiene_amigos_en_partida(partida, usuario)

@database_sync_to_async
def get_jugador_by_id(jp_id):
    """Devuelve un jugado dado su id"""
    try:
        return JugadorPartida.objects.get(id=jp_id)
    except JugadorPartida.DoesNotExist:
        return None

@database_sync_to_async
def obtener_chat_id(partida: Partida):
    """Devuelve el chat asociado a la partida"""
    return partida.get_chat_id()

@database_sync_to_async
def db_sync_to_async_save(instance):
    """Modificar instancia de la base de datos"""
    instance.save()

@database_sync_to_async
def db_sync_to_async_delete(instance):
    """Eliminar instancia de la base de datos"""
    instance.delete()

@database_sync_to_async
def refresh(instance):
    """Refrescar instancia de la base de datos"""
    instance.refresh_from_db()
    return instance

async def index_de_jugador(partida: Partida, jugador_id: int) -> int:
    """
    Retorna el índice de un jugador en la lista ordenada de jugadores, para
    sincronizar con turno_index.
    """
    jugadores = await get_jugadores(partida)
    jugadores_ordenados = sorted(jugadores, key=lambda x: x.id)
    for idx, jugador in enumerate(jugadores_ordenados):
        if jugador.id == jugador_id:
            return idx
    return 0

@database_sync_to_async
def actualizar_estadisticas(partida: Partida, ganador_equipo):
    """Actualiza las estadísticas de los jugadores al terminar la partida"""
    jugadores = list(partida.jugadores.all())
    for jugador in jugadores:
        usuario = jugador.usuario
        if ganador_equipo == 0 or jugador.equipo == ganador_equipo:
            usuario.victorias += 1
            usuario.racha_victorias += 1
            if usuario.racha_victorias > usuario.mayor_racha_victorias:
                usuario.mayor_racha_victorias = usuario.racha_victorias
        else:
            usuario.derrotas += 1
            usuario.racha_victorias = 0
        usuario.save()

def _buscar_partida_personalizada(
    usuario: Usuario,
    capacidad: int,
    solo_amigos: bool,
    tiempo_turno: int,
    permitir_revueltas: bool,
    reglas_arrastre: bool
):
    """Busca una partida personalizada con la configuración dada"""
    partidas = Partida.objects.filter(
        es_personalizada=True,
        capacidad=capacidad,
        solo_amigos=solo_amigos,
        tiempo_turno=tiempo_turno,
        permitir_revueltas=permitir_revueltas,
        reglas_arrastre=reglas_arrastre,
        estado='esperando'
    ).exclude(jugadores__usuario=usuario)
    for partida in partidas:
        num_jugadores = JugadorPartida.objects.filter(partida=partida, conectado=True).count()
        if num_jugadores < partida.capacidad:
            return partida
    return None

def _crear_partida_personalizada(
    capacidad: int,
    solo_amigos: bool,
    tiempo_turno: int,
    permitir_revueltas: bool,
    reglas_arrastre: bool
):
    """Crea una partida personalizada con la configuración dada"""
    partida = Partida(
        es_personalizada=True,
        capacidad=capacidad,
        solo_amigos=solo_amigos,
        tiempo_turno=tiempo_turno,
        permitir_revueltas=permitir_revueltas,
        reglas_arrastre=reglas_arrastre
    )
    if partida:
        partida.save()
        return partida
    return None

def _obtener_config_personalizada(params: dict):
    """Leer parámetros de la URL de conexión a una partida personalizada"""
    try:
        capacidad_value = params.get('capacidad', 2)
        if isinstance(capacidad_value, list):
            capacidad_value = str(capacidad_value[0])
        else:
            capacidad_value = str(capacidad_value)
        capacidad = 2 if int(capacidad_value) not in [2,4] else int(capacidad_value)
    except Exception as e:
        print(f"Error al obtener la capacidad: {e}")
        capacidad = 2
    
    try:
        tiempo_turno_value = params.get('tiempo_turno', 30)
        if isinstance(tiempo_turno_value, list):
            tiempo_turno_value = str(tiempo_turno_value[0])
        else:
            tiempo_turno_value = str(tiempo_turno_value)
        tiempo_turno = 30 if int(tiempo_turno_value) not in [15, 30, 60] else int(tiempo_turno_value)
    except Exception as e:
        print(f"Error al obtener el tiempo de turno: {e}")
        tiempo_turno = 30

    solo_amigos = params.get('solo_amigos', ['false'])[0].lower() == 'true'
    permitir_revueltas = params.get('permitir_revueltas', ['true'])[0].lower() == 'true'
    reglas_arrastre = params.get('reglas_arrastre', ['true'])[0].lower() == 'true'

    return capacidad, solo_amigos, tiempo_turno, permitir_revueltas, reglas_arrastre

@database_sync_to_async
def obtener_o_crear_partida_personalizada(
    usuario: Usuario,
    params: dict
):
    """
    Obtiene una partida con la configuración dada. Si no la encuentra, en su defecto,
    crea una nueva partida con dicha configuración
    """

    # Obtener y parsear parámetros de la url
    capacidad, solo_amigos, tiempo_turno, permitir_revueltas, reglas_arrastre = \
        _obtener_config_personalizada(params)
    
    # Buscar o crear partida
    p: Partida = _buscar_partida_personalizada(
        usuario, capacidad, solo_amigos, tiempo_turno, permitir_revueltas, reglas_arrastre)
    if not p:
        p = _crear_partida_personalizada(
            capacidad, solo_amigos, tiempo_turno, permitir_revueltas, reglas_arrastre)
    return p

@database_sync_to_async
def marcar_como_finalizada(partida: Partida):
    """Marcar partida como finalizada"""
    partida.marcar_como_finalizada()