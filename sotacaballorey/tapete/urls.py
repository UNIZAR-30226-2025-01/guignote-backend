from django.urls import path
from . import views

urlpatterns = [
    path('create_tapete/', views.create_tapete, name='create_tapete'),
    path('get_all_tapetes/', views.get_all_tapetes, name='get_all_tapetes'),
    path('get_tapete_id/', views.get_tapete_id_from_name, name='get_tapete_id_from_name'),
] 