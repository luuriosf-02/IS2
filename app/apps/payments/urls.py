from django.urls import path

from . import views


app_name = "payments"

urlpatterns = [
    path(
        "",
        views.lista_medios_pago,
        name="lista",
    ),
    path(
        "crear/",
        views.crear_medio_pago,
        name="crear",
    ),
    path(
        "<int:pk>/editar/",
        views.editar_medio_pago,
        name="editar",
    ),
    path(
        "<int:pk>/eliminar/",
        views.eliminar_medio_pago,
        name="eliminar",
    ),
]