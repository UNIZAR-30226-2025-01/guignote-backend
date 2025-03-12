from django.urls import path
from .views import views_individual, views_parejas

urlpatterns = [
    #individuales
    path('crear/', views_individual.crear_partida, name='crear_partida'),
    path('estado/<int:partida_id>/', views_individual.obtener_estado_partida, name='obtener_estado_partida'),
    path('alterar/<int:partida_id>/estado/', views_individual.cambiar_estado_partida, name='cambiar_estado_partida'),
    
    path('2v2/crear/', views_parejas.crear_partida, name='crear_partida_2v2'),
    path('2v2/estado/<int:partida_id>/', views_parejas.obtener_estado_partida, name='obtener_estado_partida_2v2'),
    path('2v2/alterar/<int:partida_id>/estado/', views_parejas.cambiar_estado_partida, name='cambiar_estado_partida_2v2'),
]
