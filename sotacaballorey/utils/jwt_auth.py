from django.http import JsonResponse
from usuarios.models import Usuario
from django.utils import timezone
from django.conf import settings
import datetime
import jwt

def generar_token(usuario: Usuario):
    payload = {
        'id': usuario.id,
        'nombre': usuario.nombre,
        'correo': usuario.correo,
        'exp': timezone.now() + datetime.timedelta(hours=2),
        'iat': timezone.now()
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token

def validar_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        usuario = Usuario.objects.get(id=payload['id'])
        return usuario
    except(jwt.ExpiredSignatureError, jwt.InvalidTokenError, Usuario.DoesNotExist):
        return None
    
async def validar_token_async(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        usuario = await Usuario.objects.aget(id=payload['id'])
        return usuario
    except(jwt.ExpiredSignatureError, jwt.InvalidTokenError, Usuario.DoesNotExist):
        return None

def token_required(func):
    def wrapper(request, *args, **kwargs):
        token = request.headers.get('Auth')
        
        # No está el token en la cabecera de la petición
        if not token:
            return JsonResponse({'error': 'Token no proporcionado'}, status=401)
        
        # Validamos token
        usuario = validar_token(token)
        if not usuario:
            return JsonResponse({'error': 'Token no válido o ha expirado'}, status=401)
        
        # Añadimos el usuario a la solicitud
        request.usuario = usuario
        return func(request, *args, **kwargs)

    return wrapper