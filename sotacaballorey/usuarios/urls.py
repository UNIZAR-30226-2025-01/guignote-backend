from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('crear_usuario/', views.crear_usuario, name='crear_usuario'),
    path('iniciar_sesion/', views.iniciar_sesion, name='iniciar_sesion'),
    path('eliminar_usuario/', views.eliminar_usuario, name='eliminar_usuario')
]