from partidas.models import Partida, JugadorPartida
from channels.db import database_sync_to_async
from usuarios.models import Usuario

@database_sync_to_async
def obtener_o_crear_partida(usuario: Usuario, capacidad: int, solo_amigos: bool = False):
    """
    Obtiene una partida disponible (no llena) de capacidad
    dada. Si no existe, la crea.
    Si es una partida entre amigos (solo_amigos=True), crea una nueva partida directamente.
    """
    if solo_amigos:
        partida = Partida.objects.create(capacidad=capacidad, solo_amigos=True)
        partida.save()
        return partida

    partidas_disponibles: Partida = Partida.objects.filter(
        estado='esperando', capacidad=capacidad, solo_amigos=solo_amigos
    )
    for partida in partidas_disponibles:
        if not solo_amigos or tiene_amigos_en_partida(partida, usuario):
            return partida
    partida = Partida.objects.create(capacidad=capacidad, solo_amigos=solo_amigos)
    partida.save()
    return partida

@database_sync_to_async
def obtener_partida_por_id(id_partida: str, usuario: Usuario = None):
    """
    Obtiene una partida dado su id.
    Si la partida es entre amigos y se proporciona un usuario, verifica que tenga amigos en la partida.
    """
    try:
        partida = Partida.objects.get(id=id_partida)
        if partida.solo_amigos and usuario:
            # Check friends synchronously within the database_sync_to_async context
            jugadores_ids = JugadorPartida.objects.filter(partida=partida).values_list('usuario_id', flat=True)
            amigos_ids = usuario.amigos.values_list('id', flat=True)
            tiene_amigos = any(j in amigos_ids for j in jugadores_ids) or not jugadores_ids
            if not tiene_amigos:
                return None
        return partida
    except Partida.DoesNotExist:
        return None

@database_sync_to_async
def agregar_jugador(partida: Partida, usuario: Usuario):
    """Agrega el usuario a la partida"""
    jugadores_existentes = JugadorPartida.objects.filter(partida=partida)

    if partida.solo_amigos:
        # Check friends synchronously within the database_sync_to_async context
        jugadores_ids = JugadorPartida.objects.filter(partida=partida).values_list('usuario_id', flat=True)
        amigos_ids = usuario.amigos.values_list('id', flat=True)
        tiene_amigos = any(j in amigos_ids for j in jugadores_ids) or not jugadores_ids
        if not tiene_amigos:
            return None, False

    count = jugadores_existentes.count()
    equipo = (count % 2) + 1

    jugador, created = JugadorPartida.objects.get_or_create(
        partida=partida,
        usuario=usuario,
        defaults={'equipo': equipo, 'conectado': True}
    )
    if not created:
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

@database_sync_to_async
def tiene_amigos_en_partida(partida: Partida, usuario: Usuario) -> bool:
    """
    Verifica si el usuario tiene al menos un amigo en la partida dada.
    También devuelve True si la partida está vacía (para permitir crearla).
    """
    jugadores_ids = JugadorPartida.objects.filter(partida=partida).values_list('usuario_id', flat=True)
    amigos_ids = usuario.amigos.values_list('id', flat=True)
    return any(j in amigos_ids for j in jugadores_ids) or not jugadores_ids

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
