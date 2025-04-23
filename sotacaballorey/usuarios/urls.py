from django.urls import path
from .views import views_usuarios, views_solicitudes_amistad, views_estadisticas, views_aspectos

urlpatterns = [
    # Hola, mundo (Prueba)
    path('', views_usuarios.index, name='index'),


    #######################################################################################################################################
    # Relacionadas con usuarios
    path('crear_usuario/', views_usuarios.crear_usuario, name='crear_usuario'),
    path('iniciar_sesion/', views_usuarios.iniciar_sesion, name='iniciar_sesion'),
    path('eliminar_usuario/', views_usuarios.eliminar_usuario, name='eliminar_usuario'),
    path('obtener_amigos/', views_usuarios.obtener_amigos, name='obtener_amigos'),
    path('usuarios/id/<str:username>/', views_usuarios.obtener_id_por_nombre, name="obtener_id_por_nombre"),
    path('imagen/', views_usuarios.establecer_imagen, name='establecer_imagen'),
    #######################################################################################################################################
    

    #######################################################################################################################################
    # Relacionadas con lista de amigos de usuarios
    path('enviar_solicitud_amistad/', views_solicitudes_amistad.enviar_solicitud_amistad, name="enviar_solicitud_amistad"),
    path('aceptar_solicitud_amistad/', views_solicitudes_amistad.aceptar_solicitud_amistad, name='aceptar_solicitud_amistad'),
    path('denegar_solicitud_amistad/', views_solicitudes_amistad.denegar_solicitud_amistad, name='denegar_solicitud_amistad'),
    path('listar_solicitudes_amistad/', views_solicitudes_amistad.listar_solicitudes_amistad, name='listar_solicitudes_amistad'),
    path('eliminar_amigo/', views_solicitudes_amistad.eliminar_amigo, name='eliminar_amigo'),
    path('buscar_usuarios/', views_solicitudes_amistad.buscar_usuarios, name='buscar_usuarios'),
    #######################################################################################################################################
    
    #######################################################################################################################################
    # Relacionadas con estadísticas de usuarios
    # Usuarios ajenos
    path('racha_actual/<int:user_id>/', views_estadisticas.obtener_racha_actual, name="obtener_racha_actual"),
    path('racha_mas_larga/<int:user_id>/', views_estadisticas.obtener_racha_mas_larga, name="obtener_racha_mas_larga"),
    path('partidas_totales/<int:user_id>/', views_estadisticas.obtener_total_partidas, name='obtener_total_partidas'),
    path('porcentaje_victorias/<int:user_id>/', views_estadisticas.obtener_porcentaje_victorias, name='obtener_porcentaje_victorias'),
    path('porcentaje_derrotas/<int:user_id>/', views_estadisticas.obtener_porcentaje_derrotas, name='obtener_porcentaje_derrotas'),
    path('estadisticas/<int:user_id>/', views_estadisticas.obtener_usuario_estadisticas, name='obtener_usuario_estadisticas'),
    path('elo/<int:user_id>/', views_estadisticas.obtener_elo, name="obtener_elo"),
    path('elo_parejas/<int:user_id>/', views_estadisticas.obtener_elo_parejas, name="obtener_elo_parejas"),
    
    
    # Usuario propio (usando token)
    path('racha_actual/', views_estadisticas.obtener_racha_actual_autenticado, name="obtener_racha_actual"),
    path('racha_mas_larga/', views_estadisticas.obtener_racha_mas_larga_autenticado, name="obtener_racha_mas_larga"),
    path('partidas_totales/', views_estadisticas.obtener_total_partidas_autenticado, name='obtener_total_partidas'),
    path('porcentaje_victorias/', views_estadisticas.obtener_porcentaje_victorias_autenticado, name='obtener_porcentaje_victorias'),
    path('porcentaje_derrotas/', views_estadisticas.obtener_porcentaje_derrotas_autenticado, name='obtener_porcentaje_derrotas'),
    path('estadisticas/', views_estadisticas.obtener_usuario_estadisticas_autenticado, name='obtener_usuario_estadisticas'),
    path('elo/', views_estadisticas.obtener_elo_autenticado, name="obtener_elo"),
    path('elo_parejas/', views_estadisticas.obtener_elo_parejas_autenticado, name="obtener_elo_parejas"),
    
    #rankings
    path('top_elo/', views_estadisticas.obtener_top_elo, name="obtener_top_elo"),
    path('top_elo_parejas/', views_estadisticas.obtener_top_elo_parejas, name="obtener_top_elo_parejas"),
    path('top_elo_amigos/', views_estadisticas.obtener_top_elo_amigos, name="obtener_top_elo_amigos"),
    path('top_elo_parejas_amigos/', views_estadisticas.obtener_top_elo_parejas_amigos, name="obtener_top_elo_parejas_amigos"),
    
    #######################################################################################################################################
    
    #######################################################################################################################################
    # Relacionadas con aspectos
    path('unlock_skin/<int:user_id>/', views_aspectos.unlock_skin, name='unlock_skin'),
    path('unlock_back/<int:user_id>/', views_aspectos.unlock_back, name='unlock_back'),
    path('get_unlocked_items/<int:user_id>/', views_aspectos.get_unlocked_items, name='get_unlocked_items'),
    
    #######################################################################################################################################
]