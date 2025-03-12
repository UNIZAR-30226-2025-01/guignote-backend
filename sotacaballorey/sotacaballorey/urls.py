from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('partidas/', include('partidas.urls')),
    path('mensajes/', include('chat_global.urls')),
    path('chat_partida/', include('chat_partida.urls'))
]
