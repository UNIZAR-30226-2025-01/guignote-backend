from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from utils.jwt_auth import token_required  # Import token authentication
from chat_partida.models import ChatPartidaParejas  # Updated model name
from partidas.models import Partida2v2
from usuarios.models import Usuario


@csrf_exempt
@token_required
def enviar_mensaje_chat(request, partida_id, mensaje):
    """
    Allows an authenticated user to post a chat message in a 2v2 match.
    The token must match the user sending the message.
    """
    if request.method == "POST":
        try:
            usuario = request.usuario  # Get user from token authentication

            # Validate message content
            if not mensaje:
                return JsonResponse({"error": "Message cannot be empty"}, status=400)
            

            # Get match and user
            partida = get_object_or_404(Partida2v2, id=partida_id)

            # Ensure the user is part of the match
            if usuario not in [partida.equipo_1_jugador_1, partida.equipo_1_jugador_2, 
                               partida.equipo_2_jugador_1, partida.equipo_2_jugador_2]:
                return JsonResponse({"error": "User is not part of this match"}, status=403)

            # Create the chat message
            chat_mensaje = ChatPartidaParejas.objects.create(
                partida=partida,
                usuario=usuario,
                mensaje=mensaje,
                timestamp=now()
            )

            return JsonResponse({
                "message": "Mensaje enviado",
                "mensaje_id": chat_mensaje.id,
                "usuario": usuario.nombre,
                "timestamp": chat_mensaje.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)


@csrf_exempt
@token_required
def obtener_mensajes_chat(request, partida_id):
    """
    Retrieves all messages from a 2v2 match for an authenticated user.
    The user must be part of the match.
    """
    if request.method == "GET":
        try:
            partida = get_object_or_404(Partida2v2, id=partida_id)

            # Ensure the user is part of the match
            if request.usuario not in [partida.equipo_1_jugador_1, partida.equipo_1_jugador_2, 
                                       partida.equipo_2_jugador_1, partida.equipo_2_jugador_2]:
                return JsonResponse({"error": "Unauthorized: User is not part of this match"}, status=403)

            # Retrieve chat messages in chronological order
            mensajes = ChatPartidaParejas.objects.filter(partida=partida).order_by("timestamp")

            mensajes_lista = [{
                "usuario": mensaje.usuario.nombre,
                "mensaje": mensaje.mensaje,
                "timestamp": mensaje.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            } for mensaje in mensajes]

            return JsonResponse({"mensajes": mensajes_lista}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)
