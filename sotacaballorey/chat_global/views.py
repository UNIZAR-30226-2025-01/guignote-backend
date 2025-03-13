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
        receptor_id = data.get('receptor_id')
        contenido = data.get('contenido', '').strip()

        # Mensaje vacío
        if not contenido or not receptor_id:
            return JsonResponse({'error': 'Falta algún campo'}, status=400)

        receptor = Usuario.objects.get(id=receptor_id)
        chat = obtener_o_crear_chat(request.usuario, receptor)
        if not chat:
            return JsonResponse({'error': 'Solo puedes chatear con amigos'}, status=403)
        
        # Guardar el mensaje
        Mensaje.objects.create(chat=chat, emisor=request.usuario, contenido=contenido)
        return JsonResponse({'mensaje': 'Mensaje enviado con éxito'}, status=201)
    
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
    except (json.JSONDecodeError, KeyError, ValueError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)
    

@csrf_exempt
@token_required
def obtener_mensajes(request):
    """
    Obtener todos los mensajes de un chat
    ├─ Método HTTP: GET
    ├─ Cabecera petición con Auth:<token>
    └─ Parámetros en la URL 'receptor_id'
    """

    # Error por método no permitido
    if request.method != 'GET':
        return JsonResponse({'error':'Método no permitido'}, status=405)
    
    # Obtengo id del chat
    receptor_id = request.GET.get('receptor_id')
    
    if not receptor_id:
        return JsonResponse({'error': 'Falta el receptor_id'}, status=400)

    try:
        receptor = Usuario.objects.get(id=receptor_id)
        chat = obtener_o_crear_chat(request.usuario, receptor)

        if not chat:
            return JsonResponse({'error': 'Solo puedes chatear con amigos'}, status=403)
        
        mensajes = chat.mensajes_glob.all().order_by('-fecha_envio')
        mensajes_json = [
            {
                'emisor': mensaje.emisor.id,
                'contenido': mensaje.contenido,
                'fecha_envio': mensaje.fecha_envio.strftime('%Y-%m-%d %H:%M:%S'),
            } for mensaje in mensajes
        ]
        return JsonResponse({'mensajes': mensajes_json}, status=200)
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Destinatario no encontrado'}, status=404)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'ID de destinatario inválido o datos incorrectos'}, status=400)

