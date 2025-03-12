from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from utils.jwt_auth import token_required  # Ensure this is correctly imported
from chat_global.models import ChatGlobal
from usuarios.models import Usuario

@csrf_exempt
@token_required
def enviar_mensaje_global(request, user_id, mensaje):
    """
    Allows an authenticated user to send a global message to another user.
    The sender must be the user authenticated via the token.
    """
    if request.method == "POST":
        try:
            emisor = request.usuario  # Get user from token authentication
            receptor = get_object_or_404(Usuario, id=user_id)  # Get recipient

            # Ensure the sender is not messaging themselves
            if emisor == receptor:
                return JsonResponse({"error": "Cannot send a message to yourself"}, status=400)

            # Create and save message
            chat_mensaje = ChatGlobal.objects.create(
                emisor=emisor,
                receptor=receptor,
                mensaje=mensaje,
                timestamp=now()
            )

            return JsonResponse({
                "mensaje": "Mensaje enviado",
                "mensaje_id": chat_mensaje.id,
                "emisor": emisor.nombre,
                "receptor": receptor.nombre,
                "timestamp": chat_mensaje.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)


@csrf_exempt
@token_required
def obtener_mensajes_global(request, user_id=None):
    """
    Retrieves all messages exchanged between the authenticated user and another user (if provided).
    If no user_id is given, it returns all messages sent or received by the authenticated user.
    """
    if request.method == "GET":
        try:
            usuario = request.usuario  # Get authenticated user

            # If a user_id is provided, filter messages exchanged between these two users
            if user_id:
                otro_usuario = get_object_or_404(Usuario, id=user_id)

                mensajes = ChatGlobal.objects.filter(emisor=usuario, receptor=otro_usuario) | \
                           ChatGlobal.objects.filter(emisor=otro_usuario, receptor=usuario)
            else:
                # Retrieve all messages where the authenticated user is the sender or recipient
                mensajes = ChatGlobal.objects.filter(emisor=usuario) | ChatGlobal.objects.filter(receptor=usuario)

            mensajes = mensajes.order_by("timestamp")  # Sort by oldest first

            # Serialize messages
            mensajes_serializados = [
                {
                    "emisor": msg.emisor.nombre,
                    "receptor": msg.receptor.nombre,
                    "mensaje": msg.mensaje,
                    "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                }
                for msg in mensajes
            ]

            return JsonResponse({"mensajes": mensajes_serializados}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)
