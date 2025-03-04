from django.urls import path
from .views import views_usuarios, views_solicitudes_amistad

urlpatterns = [
    # Hola, mundo (Prueba)
    path('', views_usuarios.index, name='index'),

    # Relacionadas con usuarios
    path('crear_usuario/', views_usuarios.crear_usuario, name='crear_usuario'),
    path('iniciar_sesion/', views_usuarios.iniciar_sesion, name='iniciar_sesion'),
    path('eliminar_usuario/', views_usuarios.eliminar_usuario, name='eliminar_usuario'),
    path('obtener_amigos/', views_usuarios.obtener_amigos, name='obtener_amigos'),

    # Relacionadas con lista de amigos de usuarios
    path('enviar_solicitud_amistad/', views_solicitudes_amistad.enviar_solicitud_amistad, name="enviar_solicitud_amistad"),
    path('aceptar_solicitud_amistad/', views_solicitudes_amistad.aceptar_solicitud_amistad, name='aceptar_solicitud_amistad'),
    path('listar_solicitudes_amistad/', views_solicitudes_amistad.listar_solicitudes_amistad, name='listar_solicitudes_amistad'),
    path('eliminar_amigo/', views_solicitudes_amistad.eliminar_amigo, name='eliminar_amigo'),
    path('buscar_usuarios/', views_solicitudes_amistad.buscar_usuarios, name='buscar_usuarios'),
]