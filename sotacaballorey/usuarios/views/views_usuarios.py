from django.contrib.auth.hashers import make_password, check_password
from utils.jwt_auth import generar_token, token_required
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from usuarios.models import Usuario
from django.http import JsonResponse, Http404
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
    amigos_json = [{
        'id': amigo.id,
        'nombre': amigo.nombre,
        'imagen': request.build_absolute_uri(amigo.imagen.url) if amigo.imagen else None
    } for amigo in request.usuario.amigos.all()]
    
    return JsonResponse({'amigos': amigos_json}, status=200)

@csrf_exempt
def obtener_id_por_nombre(request, username):
    """
    Retrieves the user ID based on the provided username.
    ├─ Method: GET
    ├─ URL: /usuarios/id/<str:username>/
    └─ Returns JSON: { "user_id": <id> }
    """
    try:
        usuario = get_object_or_404(Usuario, nombre=username)
        return JsonResponse({"user_id": usuario.id}, status=200)
    
    except Http404:
        return JsonResponse({"error": "User not found"}, status=404)

    except Exception as e:
        logger.error(f"Error retrieving user ID for username '{username}': {str(e)}")
        return JsonResponse({"error": "An error occurred while fetching the user ID"}, status=500)
    
@csrf_exempt
@token_required
def establecer_imagen(request):
    """
    Permite al usuario autenticado subir o actualizar su imagen de perfil
    ├─ Método HTTP: POST
    ├─ Cabecera: Auth:<token>
    ├─ Cuerpo: multipart/form-data con campo 'imagen'
    └─ Guarda la imagen redimensionada y comprimida como perfil
    """

    # Error por método no permitido
    if request.method != 'POST':
        return JsonResponse({'error':'Método no permitido'}, status=405)

    # Obtengo imagen
    f = request.FILES.get('imagen')

    # Redimensionar imagen y comprimir
    if not f or f.size > 2*1024*1024:
        return JsonResponse({'error': 'Imagen no válida'}, status=400)
    try:
        from PIL import Image
        from io import BytesIO
        from django.core.files.base import ContentFile

        i = Image.open(f).convert('RGB')
        s = 128 / min(i.size)
        i = i.resize((int(i.width*s), int(i.height*s)), Image.Resampling.LANCZOS)
        x = (i.width - 128) // 2; y = (i.height - 128) // 2
        i = i.crop((x, y, x+128, y+128))
        b = BytesIO(); i.save(b, 'WEBP', quality=75); b.seek(0)
        request.usuario.imagen.save(f"usuario_{request.usuario.id}.webp", ContentFile(b.read()), save=True)
        return JsonResponse({'mensaje': 'Imagen actualizada'}, status=200)
    except Exception as e:
        return JsonResponse({'error': 'Error procesando imagen'}, status=500)
