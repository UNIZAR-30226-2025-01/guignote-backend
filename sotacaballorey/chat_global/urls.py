from django.urls import path
from .views import views_chat_global

app_name = "chat_global"

urlpatterns = [
    path('enviar/<int:user_id>/<str:mensaje>/', views_chat_global.enviar_mensaje_global, name="enviar_mensaje_global"),
    path('mensajes/<int:user_id>/', views_chat_global.obtener_mensajes_global, name="obtener_mensajes_global"),
]
