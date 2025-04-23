
from django.urls import path
from . import views

urlpatterns = [
    path('create_card_skin/', views.create_card_skin, name='create_card_skin'),
    path('get_all_card_skins/', views.get_all_card_skins, name='get_all_card_skins'),  # New URL
]
