from .models import Chat, Mensaje, obtener_o_crear_chat
from django.views.decorators.csrf import csrf_exempt
from utils.jwt_auth import token_required
from django.http import JsonResponse
from usuarios.models import Usuario
import json

@csrf_exempt
@token_required
def enviar_mensaje(request):
    """
    Permite al usuario enviar un mensaje a un amigo
    ├─ Método HTTP: POST
    ├─ Cabecera petición con Auth:<token>
    └─ Cuerpo JSON con 'receptor_id' y 'contenido'
    """

    # Error por método no permitido
    if request.method != 'POST':
        return JsonResponse({'error':'Método no permitido'}, status=405)
    
    try:
        # Obtengo datos del cuerpo de la petición
        data = json.loads(request.body)
        receptor = Usuario.objects.get(id=data.get('receptor_id'))
        contenido = data.get('contenido', '').strip()

        # Mensaje vacío
        if not contenido:
            return JsonResponse({'error:': 'El mensaje no puede ser vacío'}, status=400)
        
        chat = obtener_o_crear_chat(request.usuario, receptor)
        if not chat:
            return JsonResponse({'error': 'Solo puedes chatear con amigos'}, status=403)
        
        # Guardar el mensaje
        mensaje = Mensaje.objects.create(chat=chat, emisor=request.usuario, contenido=contenido)
        return JsonResponse({'mensaje': 'Mensaje enviado con éxito'}, status=201)
    
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos inválidos'}, status=400)
    

@csrf_exempt
@token_required
def obtener_mensajes(request):
    """
    Obtener todos los mensajes de un chat
    ├─ Método HTTP: GET
    ├─ Cabecera petición con Auth:<token>
    └─ Parámetros en la URL 'chat_id'
    """

    # Error por método no permitido
    if request.method != 'GET':
        return JsonResponse({'error':'Método no permitido'}, status=405)
    
    # Obtengo id del chat
    chat_id = request.GET.get('chat_id')

    try:
        chat = Chat.objects.get(id=chat_id)
        # Obtengo mensajes
        mensajes = chat.mensajes_glob.all().order_by('fecha_envio')
        mensajes_json = [
            {
                'emisor': mensaje.emisor.nombre,
                'contenido': mensaje.contenido,
                'fecha_envio': mensaje.fecha_envio.strftime('%Y-%m-%d %H:%M:%S'),
            } for mensaje in mensajes
        ]
        return JsonResponse({'mensajes': mensajes_json}, status=200)

    except Chat.DoesNotExist:
        return JsonResponse({'error': 'Chat no encontrado'}, status=404)

