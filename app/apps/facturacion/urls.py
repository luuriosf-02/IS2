from django.urls import path

from . import views


app_name = "facturacion"

urlpatterns = [
    path(
        "documentos/<int:factura_id>/<str:formato>/",
        views.descargar_documento,
        name="descargar",
    ),
]