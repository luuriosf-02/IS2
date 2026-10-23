from django.urls import path
from . import views
app_name = 'cajas'
urlpatterns = [
    path('', views.lista, name='lista'),
    path('abrir/', views.apertura, name='apertura'),
    path('<int:pk>/', views.detalle, name='detalle'),
    path('<int:pk>/aceptar/', views.aceptacion, name='aceptacion'),
    path('<int:pk>/cambio/', views.cambio, name='cambio'),
    path('<int:pk>/movimiento/', views.movimiento, name='movimiento'),
    path('movimientos/<int:pk>/anular/', views.anulacion, name='anulacion'),
    path('<int:pk>/cerrar/', views.cierre, name='cierre'),
]
