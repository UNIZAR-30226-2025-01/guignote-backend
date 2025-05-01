from django.urls import path
from .views import listar_salas_disponibles, listar_salas_reconectables, listar_salas_amigos

urlpatterns = [
    path('disponibles/amigos/', listar_salas_amigos, name='salas_disponibles_amigos'),
    path('disponibles/', listar_salas_disponibles, name='salas_disponibles'),
    path('reconectables/', listar_salas_reconectables, name='salas_reconectables')
]