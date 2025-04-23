from django.urls import path
from . import views

urlpatterns = [
    path('create_card_back/', views.create_card_back, name='create_card_back'),
    path('get_all_card_backs/', views.get_all_card_backs, name='get_all_card_backs'),
    path('get_card_back_id/', views.get_card_back_id_from_name, name='get_card_back_id_from_name'),
]
