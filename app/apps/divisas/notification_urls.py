from django.urls import path
from . import notification_views as views
app_name = 'notificaciones'
urlpatterns = [
    path('', views.lista, name='lista'),
    path('leer-todas/', views.leer_todas, name='leer_todas'),
    path('<int:pk>/leer/', views.leer, name='leer'),
]
