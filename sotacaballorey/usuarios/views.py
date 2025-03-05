from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import get_object_or_404
from utils.jwt_auth import generar_token, token_required
from django.views.decorators.csrf import csrf_exempt
from .models import Usuario, SolicitudAmistad
from django.http import JsonResponse
import json
import logging

# Setup logging to capture errors
logger = logging.getLogger(__name__)

@csrf_exempt
def index(request):
    """
    Función de entrada. Prueba mensaje de bienvenida.
    """
    return JsonResponse({'mensaje': 'Hola, unizar!'}, status=200)

@csrf_exempt
def crear_usuario(request):
    """
    Crea un nuevo usuario.
    ├─ Método HTTP: POST
    ├─ Cuerpo JSON con 'nombre', 'correo' y 'contrasegna'
    └─ Si todo correcto, encripta contraseña y devuelve un token jwt
    """

    # Error por método no permitido
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Obtengo datos del cuerpo de la petición
    data = json.loads(request.body)
    nombre = data.get('nombre')
    correo = data.get('correo')
    contrasegna = data.get('contrasegna')

    # Error por campo vacío
    if not nombre or not correo or not contrasegna:
        return JsonResponse({'error': 'Faltan campos'}, status=400)
    
    # Error por correo o nombre ya en uso
    if Usuario.objects.filter(correo=correo).exists() or \
        Usuario.objects.filter(nombre=nombre).exists():
        return JsonResponse({'error': 'Correo o nombre ya en uso'}, status=400)
    
    # Creamos usuario e introducimos en nuestra bbdd
    usuario = Usuario(
        nombre=nombre,
        correo=correo,
        contrasegna=make_password(contrasegna)
    )
    usuario.save()

    # Creación de usuario exitosa, le doy token jwt
    return JsonResponse({'token': generar_token(usuario)}, status=201)

@csrf_exempt
def iniciar_sesion(request):
    """
    Inicia sesión de un usuario
    ├─ Método HTTP: POST
    ├─ Cuerpo JSON con ('nombre' o 'correo') y 'contrasegna'
    └─ Si todo correcto, devuelve un token jwt
    """

    # Error por método no permitido
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Obtengo datos del cuerpo de la petición
    data = json.loads(request.body)
    nombre = data.get('nombre')
    correo = data.get('correo')
    contrasegna = data.get('contrasegna')

    # Error por campo vacío
    if not contrasegna or (not nombre and not correo):
        return JsonResponse({'error': 'Faltan campos'}, status=400)
    
    # Verificar si usuario existe
    usuario: Usuario = None
    try:
        if not nombre:
            usuario = Usuario.objects.get(correo=correo)
        else:
            usuario = Usuario.objects.get(nombre=nombre)
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
    
    # Verificar la contraseña
    if not check_password(contrasegna, usuario.contrasegna):
        return JsonResponse({'error': 'Contraseña incorrecta'}, status=400)
    
    # Inicio de sesión existoso, le doy token jwt
    return JsonResponse({'token': generar_token(usuario)}, status=201)

@csrf_exempt
@token_required
def eliminar_usuario(request):
    """
    Elimina usuario autenticado.
    ├─ Método HTTP: DELETE
    ├─ Cabecera petición con Auth:<token>
    └─ Elimina el usuario de la base de datos
    """

    # Error por método no permitido
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    # Borrar usuario
    usuario = request.usuario
    usuario.delete()

    # Borrado usuario exitoso
    return JsonResponse({'mensaje': 'Usuario eliminado con éxito'}, status=200)

@csrf_exempt
@token_required
def enviar_solicitud_amistad(request):
    """
    Envía una solicitud de amistad
    ├─ Método HTTP: POST
    ├─ Cabecera petición con Auth:<token>
    ├─ Cuerpo JSON con 'destinatario_id'
    └─ Si todo correcto, crea solicitud de amistad
    """

    # Error por método no permitido
    if request.method != 'POST':
        return JsonResponse({'error':'Método no permitido'}, status=405)
    
    # Obtengo datos del cuerpo de la petición
    data = json.loads(request.body)
    destinatario_id = data.get('destinatario_id')

    # Error por campo vacío
    if not destinatario_id:
        return JsonResponse({'error': 'Faltan campos'}, status=400)

    # Verificar que destinatario de la solicitud existe
    destinatario: Usuario = None
    try:
        destinatario = Usuario.objects.get(id=destinatario_id)
    except Usuario.DoesNotExist:
        return JsonResponse({'error':'Destinatario no encontrado'}, status=404)
    
    # Verificar que el usuario no se envíe solicitud a sí mismo
    if request.usuario == destinatario:
        return JsonResponse({'error': 'No puedes enviarte una solicitud a ti mismo'}, status=400)

    # Verificar que la solicitud todavía no existe
    if SolicitudAmistad.objects.filter(emisor=request.usuario, receptor=destinatario).exists():
        return JsonResponse({'error':'La solicitud ya fue enviada'}, status=400)

    # Registrar solicitud de amistad
    solicitud = SolicitudAmistad(emisor=request.usuario, receptor=destinatario)
    solicitud.save()
    return JsonResponse({'mensaje':'Solicitud enviada con éxito'}, status=201)

@csrf_exempt
@token_required
def aceptar_solicitud_amistad(request):
    """
    Acepta una solicitud de amistad
    ├─ Método HTTP: POST
    ├─ Cabecera petición con Auth:<token>
    ├─ Cuerpo JSON con 'solicitud_id'
    └─ Si todo correcto, elimina solicitud y añade el remitente a lista de amigos
    """

    # Error por método no permitido
    if request.method != 'POST':
        return JsonResponse({'error':'Método no permitido'}, status=405)

    # Obtengo datos del cuerpo de la petición
    data = json.loads(request.body)
    solicitud_id = data.get('solicitud_id')

    # Error por campo vacío
    if not solicitud_id:
        return JsonResponse({'error': 'Faltan campos'}, status=400)

    # Verificar que solicitud existe
    solicitud: SolicitudAmistad = None
    try:
        solicitud = SolicitudAmistad.objects.get(id=solicitud_id)
    except SolicitudAmistad.DoesNotExist:
        return JsonResponse({'error':'Solicitud no encontrada'}, status=404)

    if solicitud.receptor != request.usuario:
        return JsonResponse({'error':'No puedes aceptar una solicitud que no te pertenece'}, status=403)

    # Quitar la solicitud de bbdd y añadir amigos
    solicitud.emisor.amigos.add(solicitud.receptor)
    solicitud.delete()

    return JsonResponse({'mensaje':'Solicitud aceptada con éxito'}, status=200)

@csrf_exempt
@token_required
def listar_solicitudes_amistad(request):
    """
    Lista solicitudes de amistad pendientes del usuario autenticado
    ├─ Método HTTP: GET
    ├─ Cabecera petición con Auth:<token>
    └─ Devuelve lista solicitudes de amistad pendientes
    """

    # Error por método no permitido
    if request.method != 'GET':
        return JsonResponse({'error':'Método no permitido'}, status=405)

    # Obtener solicitudes pendientes
    solicitudes = SolicitudAmistad.objects.filter(receptor=request.usuario)
    solicitudes_json = [{'id': s.id, 'solicitante': s.emisor.nombre} for s in solicitudes]
    
    return JsonResponse({'solicitudes': solicitudes_json}, status=200)

@csrf_exempt
@token_required
def eliminar_amigo(request):
    """
    Elimina un amigo de la lista de amigos de un usuario autenticado
    ├─ Método HTTP: DELETE
    ├─ Cabecera petición con Auth:<token>
    ├─ Cuerpo JSON con 'amigo_id'
    └─ Verifica si amigo existe y lo elimina de la relación
    """

    # Error por método no permitido
    if request.method != 'DELETE':
        return JsonResponse({'error':'Método no permitido'}, status=405)

    # Obtengo datos del cuerpo de la petición
    data = json.loads(request.body)
    amigo_id = data.get('amigo_id')  

    # Error por campo vacío
    if not amigo_id:
        return JsonResponse({'error': 'Faltan campos'}, status=400)

    # Verificar que amigo existe
    amigo: Usuario = None
    try:
        amigo = Usuario.objects.get(id=amigo_id)
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Amigo no encontrado'}, status=404)

    # Quitar amigo
    request.usuario.amigos.remove(amigo)

    return JsonResponse({'mensaje': 'Amigo eliminado con éxito'}, status=200)

@csrf_exempt
@token_required
def obtener_amigos(request):
    """
    Obtiene lista de amigos de usuario autenticado
    ├─ Método HTTP: GET
    ├─ Cabecera petición con Auth:<token>
    └─ Devuelve lista de amigos con su id y nombre
    """

    # Error por método no permitido
    if request.method != 'GET':
        return JsonResponse({'error':'Método no permitido'}, status=405)

    # Obtener amigos
    amigos_json = [{'id': amigo.id, 'nombre': amigo.nombre} for amigo in request.usuario.amigos.all()]
    
    return JsonResponse({'amigos': amigos_json}, status=200)

@csrf_exempt
@token_required
def buscar_usuarios(request):
    """
    Busca usuarios por nombre
    ├─ Método HTTP: GET
    ├─ Cabecera petición con Auth:<token>
    ├─ Cuerpo JSON con 'nombre' y 'incluir_amigos'
    └─ Devuelve lista de usuarios con su id y nombre
    """

    # Error por método no permitido
    if request.method != 'GET':
        return JsonResponse({'error':'Método no permitido'}, status=405)

    # Obtenemos parámetros
    nombre = request.GET.get('nombre', '')
    incluir_amigos = request.GET.get('incluir_amigos', 'false').lower() == 'true'

    # Obtenemos usuarios cuyo nombre contenga 'nombre'. Si incluir_amigos es falso
    # no incluiremos en el resultado a los amigos, aunque cumplan la restricción
    usuarios = Usuario.objects.filter(nombre__icontains=nombre)
    if not incluir_amigos:
        usuarios = usuarios.exclude(id__in=request.usuario.amigos.all())

    usuarios_json = [{'id': u.id, 'nombre': u.nombre} for u in usuarios]

    return JsonResponse({'usuarios': usuarios_json}, status=200)

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
            "porcentaje_derrotas": loss_percentage
        }

        return JsonResponse(estadisticas)
    
    except Exception as e:
        logger.error(f"Error retrieving statistics for user {user_id}: {str(e)}")
        return JsonResponse({"error": "An error occurred while fetching user statistics"}, status=500)