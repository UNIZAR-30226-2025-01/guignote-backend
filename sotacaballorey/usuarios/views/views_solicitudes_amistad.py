from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import get_object_or_404
from utils.jwt_auth import generar_token, token_required
from django.views.decorators.csrf import csrf_exempt
from usuarios.models import Usuario, SolicitudAmistad
from django.http import JsonResponse
from django.db.models import Q
import json
import logging

# Setup logging to capture errors
logger = logging.getLogger(__name__)

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
def denegar_solicitud_amistad(request):
    """
    Quita una solicitud de amistad
    ├─ Método HTTP: POST
    ├─ Cabecera petición con Auth:<token>
    ├─ Cuerpo JSON con 'solicitud_id'
    └─ Si todo correcto, elimina solicitud
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
        return JsonResponse({'error':'No puedes denegar una solicitud que no te pertenece'}, status=403)

    # Quitar la solicitud de bbdd
    solicitud.delete()

    return JsonResponse({'mensaje':'Solicitud denegada con éxito'}, status=200)

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
    amigo_id = request.GET.get('amigo_id')

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
def buscar_usuarios(request):
    """
    Busca usuarios por nombre
    ├─ Método HTTP: GET
    ├─ Cabecera petición con Auth:<token>
    ├─ Cuerpo JSON con 'nombre', 'incluir_amigos', 'incluir_me', 'incluir_pendientes'
    └─ Devuelve lista de usuarios con su id y nombre
    """

    # Error por método no permitido
    if request.method != 'GET':
        return JsonResponse({'error':'Método no permitido'}, status=405)

    # Obtenemos parámetros
    nombre = request.GET.get('nombre', '').strip()
    incluir_amigos = request.GET.get('incluir_amigos', 'false').lower() == 'true'
    incluir_me = request.GET.get('incluir_me', 'false').lower() == 'true'
    incluir_pendientes = request.GET.get('incluir_pendientes', 'false').lower() == 'true'

    # Filtro usuarios cuyo nombre contenga 'nombre'
    filtros = Q(nombre__icontains=nombre)

    # Excluimos amigos si incluir_amigos es falso
    if not incluir_amigos:
        amigos_ids = request.usuario.amigos.values_list('id', flat=True)
        filtros &= ~Q(id__in=amigos_ids)

    # Excluirme a mi mismo si incluir_me es falso
    if not incluir_me:
        filtros &= ~Q(id=request.usuario.id)

    # Excluir usuarios con solicitudes pendientes mías de aceptar
    if not incluir_pendientes:
        solicitudes_pendientes = SolicitudAmistad.objects.filter(
            emisor=request.usuario).values_list('receptor_id', flat=True)
        filtros &= ~Q(id__in=solicitudes_pendientes)

    # Aplicar filtro
    usuarios = Usuario.objects.filter(filtros)
    
    # Convertir a JSON
    usuarios_json = [{'id': u.id, 'nombre': u.nombre} for u in usuarios]

    return JsonResponse({'usuarios': usuarios_json}, status=200)
