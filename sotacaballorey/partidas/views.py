from django.views.decorators.csrf import csrf_exempt
from utils.jwt_auth import token_required
from django.http import JsonResponse
from django.db.models import Count
from .models import Partida

@csrf_exempt
@token_required
def listar_salas_disponibles(request):
    """
    Lista de salas disponibles para unirse (estado 'esperando' y no llenas)
    ├─ Método HTTP: GET
    ├─ Cabecera petición con Auth:<token>
    ├─ QueryParam opcional: capacidad (2|4)
    └─ Devuelve lista de salas disponibles con ID, nombre, capacidad y jugadores actuales
    """

    # Método incorrecto
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Obtener parámetros de la URL
    capacidad = request.GET.get('capacidad')

    if capacidad == '2':
        partidas = Partida.objects.filter(
            estado='esperando', capacidad=2, solo_amigos=False)
    elif capacidad == '4':
        partidas = Partida.objects.filter(
            estado='esperando', capacidad=4, solo_amigos=False)
    else:
        partidas = Partida.objects.filter(
            estado='esperando', solo_amigos=False)

    partidas = partidas.exclude(jugadores__usuario=request.usuario)
    partidas = partidas.annotate(num_jugadores=Count('jugadores'))

    # Devolver salas
    salas_json = [
        construir_sala_json(p)
    for p in partidas]

    return JsonResponse({'salas': salas_json}, status=200)

@csrf_exempt
@token_required
def listar_salas_reconectables(request):
    """
    Lista de salas en las que el usuario estaba jugando y se desconectó
    ├─ Método HTTP: GET
    ├─ Cabecera petición con Auth:<token>
    └─ Devuelve lista de salas 'jugando' donde el usuario no está conectado
    """

    # Método incorrecto
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    partidas = Partida.objects.filter(
        estado='jugando',
        jugadores__usuario=request.usuario,
        jugadores__conectado=False
    ).annotate(num_jugadores=Count('jugadores'))

    # Devolver salas
    salas_json = [
        construir_sala_json(p)
    for p in partidas]

    return JsonResponse({'salas': salas_json}, status=200)

@csrf_exempt
@token_required
def listar_salas_pausadas(request):
    """
    Lista de salas pausadas
    ├─ Método HTTP: GET
    ├─ Cabecera petición con Auth:<token>
    └─ Devuelve lista de salas 'pausadas'
    """

    # Método incorrecto
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    partidas = Partida.objects.filter(
        estado='pausada',
        jugadores__usuario=request.usuario
    ).annotate(num_jugadores=Count('jugadores'))

    # Devolver salas
    salas_json = [
        construir_sala_json(p)
    for p in partidas]

    return JsonResponse({'salas': salas_json}, status=200)

@csrf_exempt
@token_required
def listar_salas_amigos(request):
    """
    Lista de salas con amigos disponibles para unirse
    ├─ Método HTTP: GET
    ├─ Cabecera petición con Auth:<token>
    └─ Devuelve salas donde haya al menos un amigo y el usuario aún no esté
    """

    # Método incorrecto
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    usuario = request.usuario
    amigos = usuario.amigos.all()

    # Partidas en espera donde hay al menos un amigo y el usuario no está
    partidas = Partida.objects.filter(
        estado='esperando',
        jugadores__usuario__in=amigos
    ).exclude(
        jugadores__usuario=usuario
    ).annotate(
        num_jugadores=Count('jugadores')
    ).distinct()

    # Listar salas
    salas_json = [
        construir_sala_json(p)
    for p in partidas]

    return JsonResponse({'salas': salas_json}, status=200)

def construir_sala_json(partida: Partida, amigos=None):
    """
    Te devuelve la información de una sala en formato JSON
    Añade información extra si la partida es personalizada
    """
    jugadores = partida.jugadores.all()
    nombre_jugadores = [j.usuario.nombre for j in jugadores]

    sala = {
        'id': partida.id,
        'nombre': f'Sala {partida.id}',
        'capacidad': partida.capacidad,
        'num_jugadores': partida.num_jugadores,
        'jugadores': nombre_jugadores
    }

    if partida.es_personalizada:
        sala['personalizacion'] = {
            'tiempo_turno': partida.tiempo_turno,
            'reglas_arrastre': partida.reglas_arrastre,
            'permitir_revueltas': partida.permitir_revueltas,
            'solo_amigos': partida.solo_amigos
        }
    
    return sala
