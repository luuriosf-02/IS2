from django.urls import path
from . import views

urlpatterns = [
    path('gestion-tasas/', 
         views.gestion_divisas_view, 
         name='gestion_divisas'),
         
    path('transaccion/<str:transaccion_id>/cancelar/', 
         views.cancelar_transaccion, 
         name='cancelar_transaccion'),
]