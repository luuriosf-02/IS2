from django.urls import path
from .views import gestion_divisas_view

urlpatterns = [
    path('gestion-tasas/', 
         gestion_divisas_view, 
         name='gestion_divisas'),
]