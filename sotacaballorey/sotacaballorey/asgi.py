import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sotacaballorey.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from chat_global.routing import websocket_urlpatterns
from chat_partida.routing import websocket_urlpatterns_partida
from django.contrib.auth.models import AnonymousUser
from django.core.asgi import get_asgi_application
from utils.jwt_auth import validar_token_async
from urllib.parse import parse_qs

class TokenAuthMiddleware:
    """
    Middleware para autenticar WebSockets usando el token
    """
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        parametros = parse_qs(query_string)
        token = parametros.get('token', [None])[0]


        if not token:
            print("No se encontró token en la URL. Cerrando conexión", flush=True)
            await send({'type': 'websocket.close', 'code': 403})
            return
        
        usuario = await validar_token_async(token)
        

        if usuario:
            print(f"Usuario {usuario.nombre} autenticado en WebSocket", flush=True)
            scope['usuario'] = usuario
        else:
            print(f"Token inválido o expirado. Cerrando conexión", flush=True)
            scope['usuario'] = AnonymousUser()
            return

        return await self.inner(scope, receive, send)


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TokenAuthMiddleware(
        URLRouter(websocket_urlpatterns + websocket_urlpatterns_partida))
})