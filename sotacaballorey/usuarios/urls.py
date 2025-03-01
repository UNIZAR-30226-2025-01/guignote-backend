from django.urls import path
from . import views

urlpatterns = [
    # Relacionadas con usuarios
    path('', views.index, name='index'),
    path('crear_usuario/', views.crear_usuario, name='crear_usuario'),
    path('iniciar_sesion/', views.iniciar_sesion, name='iniciar_sesion'),
    path('eliminar_usuario/', views.eliminar_usuario, name='eliminar_usuario'),
    # Relacionadas con lista de amigos de usuarios
    path('enviar_solicitud_amistad/', views.enviar_solicitud_amistad, name='enviar_solicitud_amistad'),
    path('aceptar_solicitud_amistad/', views.aceptar_solicitud_amistad, name='aceptar_solicitud_amistad'),
    path('listar_solicitudes_amistad/', views.listar_solicitudes_amistad, name='listar_solicitudes_amistad'),
    path('eliminar_amigo/', views.eliminar_amigo, name='eliminar_amigo'),
    path('obtener_amigos/', views.obtener_amigos, name='obtener_amigos'),
    path('buscar_usuarios/', views.buscar_usuarios, name='buscar_usuarios'),
]