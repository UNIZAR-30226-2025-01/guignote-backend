from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('mensajes/', include('chat_global.urls')),
    path('salas/', include('partidas.urls')),
    path('chat_partida/', include('chat_partida.urls')),
    path('aspectos/', include('dorso_carta.urls')),
    path('aspectos/', include('aspecto_carta.urls')),
    path('aspectos/', include('tapete.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
