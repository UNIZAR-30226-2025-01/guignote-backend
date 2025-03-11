from django.contrib.auth.hashers import make_password, check_password
from utils.jwt_auth import generar_token, token_required
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from usuarios.models import Usuario
from django.http import JsonResponse
import json
import logging

# Setup logging to capture errors
logger = logging.getLogger(__name__)

@csrf_exempt
def obtener_total_partidas(request, user_id):
    """Returns the total number of games played by a user."""
    try:
        usuario = get_object_or_404(Usuario, id=user_id)
        total_partidas = usuario.victorias + usuario.derrotas
        return JsonResponse({"user": usuario.nombre, "total_partidas": total_partidas})
    except Exception as e:
        logger.error(f"Error retrieving total games for user {user_id}: {str(e)}")
        return JsonResponse({"error": "An error occurred while fetching total games"}, status=500)

@csrf_exempt
def obtener_porcentaje_victorias(request, user_id):
    """Returns the win percentage of a user."""
    try:
        usuario = get_object_or_404(Usuario, id=user_id)
        total_games = usuario.victorias + usuario.derrotas

        if total_games == 0:
            return JsonResponse({"user": usuario.nombre, "porcentaje_victorias": 0.0})

        win_percentage = round((usuario.victorias / total_games) * 100, 2)
        return JsonResponse({"user": usuario.nombre, "porcentaje_victorias": win_percentage})

    except Exception as e:
        logger.error(f"Error retrieving win percentage for user {user_id}: {str(e)}")
        return JsonResponse({"error": "An error occurred while fetching win percentage"}, status=500)

@csrf_exempt
def obtener_porcentaje_derrotas(request, user_id):
    """Returns the loss percentage of a user."""
    try:
        usuario = get_object_or_404(Usuario, id=user_id)
        total_games = usuario.victorias + usuario.derrotas

        if total_games == 0:
            return JsonResponse({"user": usuario.nombre, "porcentaje_derrotas": 0.0})

        loss_percentage = round((usuario.derrotas / total_games) * 100, 2)
        return JsonResponse({"user": usuario.nombre, "porcentaje_derrotas": loss_percentage})

    except Exception as e:
        logger.error(f"Error retrieving loss percentage for user {user_id}: {str(e)}")
        return JsonResponse({"error": "An error occurred while fetching loss percentage"}, status=500)

@csrf_exempt
def obtener_racha_actual(request, user_id):
    """Returns the current winning streak of a user."""
    try:
        usuario = get_object_or_404(Usuario, id=user_id)
        return JsonResponse({"user": usuario.nombre, "racha_victorias": usuario.racha_victorias})

    except Exception as e:
        logger.error(f"Error retrieving current streak for user {user_id}: {str(e)}")
        return JsonResponse({"error": "An error occurred while fetching current winning streak"}, status=500)
# Setup logging to capture errors
logger = logging.getLogger(__name__)
@csrf_exempt
def obtener_racha_mas_larga(request, user_id):
    """Returns the longest winning streak of a user."""
    try:
        usuario = get_object_or_404(Usuario, id=user_id)
        return JsonResponse({"user": usuario.nombre, "mayor_racha_victorias": usuario.mayor_racha_victorias})

    except Exception as e:
        logger.error(f"Error retrieving longest streak for user {user_id}: {str(e)}")
        return JsonResponse({"error": "An error occurred while fetching longest winning streak"}, status=500)

@csrf_exempt
def obtener_usuario_estadisticas(request, user_id):
    """Returns all user statistics in a single JSON response."""
    try:
        usuario = get_object_or_404(Usuario, id=user_id)

        total_games = usuario.victorias + usuario.derrotas
        win_percentage = round((usuario.victorias / total_games) * 100, 2) if total_games > 0 else 0.0
        loss_percentage = round((usuario.derrotas / total_games) * 100, 2) if total_games > 0 else 0.0

        estadisticas = {
            "nombre": usuario.nombre,
            "victorias": usuario.victorias,
            "derrotas": usuario.derrotas,
            "racha_victorias": usuario.racha_victorias,
            "mayor_racha_victorias": usuario.mayor_racha_victorias,
            "total_partidas": total_games,
            "porcentaje_victorias": win_percentage,
            "porcentaje_derrotas": loss_percentage,
            "elo": usuario.elo
        }

        return JsonResponse(estadisticas)
    
    except Exception as e:
        logger.error(f"Error retrieving statistics for user {user_id}: {str(e)}")
        return JsonResponse({"error": "An error occurred while fetching user statistics"}, status=500)
    


@csrf_exempt
@token_required
def obtener_total_partidas_autenticado(request):
    """Returns the total number of games played by the authenticated user."""
    try:
        usuario = request.usuario  # Extract user from token
        total_partidas = usuario.victorias + usuario.derrotas
        return JsonResponse({"user": usuario.nombre, "total_partidas": total_partidas})

    except Exception as e:
        logger.error(f"Error retrieving total games for user {usuario.id}: {str(e)}")
        return JsonResponse({"error": "An error occurred while fetching total games"}, status=500)


@csrf_exempt
@token_required
def obtener_porcentaje_victorias_autenticado(request):
    """Returns the win percentage of the authenticated user."""
    try:
        usuario = request.usuario
        total_games = usuario.victorias + usuario.derrotas

        win_percentage = round((usuario.victorias / total_games) * 100, 2) if total_games > 0 else 0.0
        return JsonResponse({"user": usuario.nombre, "porcentaje_victorias": win_percentage})

    except Exception as e:
        logger.error(f"Error retrieving win percentage for user {usuario.id}: {str(e)}")
        return JsonResponse({"error": "An error occurred while fetching win percentage"}, status=500)


@csrf_exempt
@token_required
def obtener_porcentaje_derrotas_autenticado(request):
    """Returns the loss percentage of the authenticated user."""
    try:
        usuario = request.usuario
        total_games = usuario.victorias + usuario.derrotas

        loss_percentage = round((usuario.derrotas / total_games) * 100, 2) if total_games > 0 else 0.0
        return JsonResponse({"user": usuario.nombre, "porcentaje_derrotas": loss_percentage})

    except Exception as e:
        logger.error(f"Error retrieving loss percentage for user {usuario.id}: {str(e)}")
        return JsonResponse({"error": "An error occurred while fetching loss percentage"}, status=500)


@csrf_exempt
@token_required
def obtener_racha_actual_autenticado(request):
    """Returns the current winning streak of the authenticated user."""
    try:
        usuario = request.usuario
        return JsonResponse({"user": usuario.nombre, "racha_victorias": usuario.racha_victorias})

    except Exception as e:
        logger.error(f"Error retrieving current streak for user {usuario.id}: {str(e)}")
        return JsonResponse({"error": "An error occurred while fetching current winning streak"}, status=500)


@csrf_exempt
@token_required
def obtener_racha_mas_larga_autenticado(request):
    """Returns the longest winning streak of the authenticated user."""
    try:
        usuario = request.usuario
        return JsonResponse({"user": usuario.nombre, "mayor_racha_victorias": usuario.mayor_racha_victorias})

    except Exception as e:
        logger.error(f"Error retrieving longest streak for user {usuario.id}: {str(e)}")
        return JsonResponse({"error": "An error occurred while fetching longest winning streak"}, status=500)
    
@csrf_exempt
@token_required
def obtener_elo(request, user_id):
    """
    Devuelve el Elo actual de un usuario.
    """
    if request.method == "GET":
        usuario = get_object_or_404(Usuario, id=user_id)
        return JsonResponse({"user": usuario.nombre, "elo": usuario.elo}, status=200)

    return JsonResponse({"error": "Método no permitido"}, status=405)

@csrf_exempt
@token_required
def obtener_elo_autenticado(request):
    """
    Devuelve el Elo actual del usuario autenticado.
    El usuario autenticado se obtiene del token.
    """
    if request.method == "GET":
        usuario = request.usuario  # Usuario autenticado extraído del token
        return JsonResponse({"user": usuario.nombre, "elo": usuario.elo}, status=200)

    return JsonResponse({"error": "Método no permitido"}, status=405)


@csrf_exempt
@token_required
def obtener_usuario_estadisticas_autenticado(request):
    """Returns all user statistics for the authenticated user."""
    try:
        usuario = request.usuario

        total_games = usuario.victorias + usuario.derrotas
        win_percentage = round((usuario.victorias / total_games) * 100, 2) if total_games > 0 else 0.0
        loss_percentage = round((usuario.derrotas / total_games) * 100, 2) if total_games > 0 else 0.0

        estadisticas = {
            "nombre": usuario.nombre,
            "victorias": usuario.victorias,
            "derrotas": usuario.derrotas,
            "racha_victorias": usuario.racha_victorias,
            "mayor_racha_victorias": usuario.mayor_racha_victorias,
            "total_partidas": total_games,
            "porcentaje_victorias": win_percentage,
            "porcentaje_derrotas": loss_percentage,
            "elo": usuario.elo
        }

        return JsonResponse(estadisticas)

    except Exception as e:
        logger.error(f"Error retrieving statistics for user {usuario.id}: {str(e)}")
        return JsonResponse({"error": "An error occurred while fetching user statistics"}, status=500)
    
