from django.urls import path
from .views import listar_salas_disponibles, listar_salas_reconectables

urlpatterns = [
    path('disponibles/', listar_salas_disponibles, name='salas_disponibles'),
    path('reconectables/', listar_salas_reconectables, name='salas_reconectables'),
]