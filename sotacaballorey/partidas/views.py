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
        partidas = Partida.objects.filter(estado='esperando', capacidad=2)
    elif capacidad == '4':
        partidas = Partida.objects.filter(estado='esperando', capacidad=4)
    else:
        partidas = Partida.objects.filter(estado='esperando')

    partidas = partidas.annotate(num_jugadores=Count('jugadores'))

    # Devolver salas
    salas_json = [{
        'id': p.id,
        'nombre': f'Sala {p.id}',
        'capacidad': p.capacidad,
        'num_jugadores': p.num_jugadores
    } for p in partidas]

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
    salas_json = [{
        'id': p.id,
        'nombre': f'Sala {p.id}',
        'capacidad': p.capacidad,
        'num_jugadores': p.num_jugadores
    } for p in partidas]

    return JsonResponse({'salas': salas_json}, status=200)