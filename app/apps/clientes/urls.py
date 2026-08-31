from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('', views.lista_clientes, name='lista'),
    path('crear/', views.crear_cliente, name='crear'),
    path('<int:pk>/', views.detalle_cliente, name='detalle'),
    path('<int:pk>/editar/', views.editar_cliente, name='editar'),
]
