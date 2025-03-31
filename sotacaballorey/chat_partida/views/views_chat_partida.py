from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from utils.jwt_auth import token_required
from chat_partida.models import MensajePartida, Chat_partida as Chat
from usuarios.models import Usuario
import json

@csrf_exempt
@token_required
def enviar_mensaje(request):
    """
    Permite al usuario enviar un mensaje a un chat específico usando chat_id.
    ├─ Método HTTP: POST
    ├─ Cabecera petición con Auth:<token>
    └─ Cuerpo JSON con 'chat_id' y 'contenido'
    """
    # Error por método no permitido
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Obtengo datos del cuerpo de la petición
        data = json.loads(request.body)
        chat_id = data.get('chat_id')
        contenido = data.get('contenido', '').strip()

        # Validar campos requeridos
        if not contenido or not chat_id:
            return JsonResponse({'error': 'Falta algún campo'}, status=400)

        # Obtener el chat por chat_id
        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            return JsonResponse({'error': 'Chat no encontrado'}, status=404)

        # Check if the user is a participant in the chat
        user = request.usuario
        if user not in chat.participants.all():
            return JsonResponse({'error': 'User is not a participant in this chat'}, status=403)

        # Crear el mensaje en el chat
        MensajePartida.objects.create(
            emisor=user,
            contenido=contenido,
            chat=chat  # Asociar el mensaje con el chat usando el chat_id
        )
        
        return JsonResponse({'mensaje': 'Mensaje enviado con éxito'}, status=201)
    
    except (json.JSONDecodeError, KeyError, ValueError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

@csrf_exempt
@token_required
def obtener_mensajes(request):
    """
    Obtener todos los mensajes de un chat específico usando chat_id.
    ├─ Método HTTP: GET
    ├─ Cabecera petición con Auth:<token>
    └─ Parámetro en la URL 'chat_id'
    """
    # Error por método no permitido
    if request.method != 'GET':
        return JsonResponse({'error':'Método no permitido'}, status=405)
    
    # Obtengo el parámetro chat_id de la URL
    chat_id = request.GET.get('chat_id')
    
    if not chat_id:
        return JsonResponse({'error': 'Falta parámetro chat_id'}, status=400)

    try:
        # Obtener el chat por chat_id
        chat = Chat.objects.get(id=chat_id)
        
        # Check if the user is a participant in the chat
        user = request.usuario
        if user not in chat.participants.all():
            return JsonResponse({'error': 'User is not a participant in this chat'}, status=403)

        # Obtener todos los mensajes asociados al chat
        mensajes = MensajePartida.objects.filter(chat=chat).order_by('-fecha_envio')
        
        if not mensajes:
            return JsonResponse({'error': 'No hay mensajes para este chat'}, status=404)

        # Preparar los mensajes para la respuesta
        mensajes_json = [
            {
                'emisor': mensaje.emisor.id,
                'contenido': mensaje.contenido,
                'fecha_envio': mensaje.fecha_envio.strftime('%Y-%m-%d %H:%M:%S'),
            } for mensaje in mensajes
        ]
        
        return JsonResponse({'mensajes': mensajes_json}, status=200)

    except Chat.DoesNotExist:
        return JsonResponse({'error': 'Chat no encontrado'}, status=404)

    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Datos incorrectos'}, status=400)
