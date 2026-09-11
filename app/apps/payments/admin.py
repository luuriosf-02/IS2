from django.contrib import admin

from .models import MedioPago


@admin.register(MedioPago)
class MedioPagoAdmin(admin.ModelAdmin):
    list_display = (
        "cliente",
        "tipo",
        "marca",
        "ultimos_cuatro",
        "alias",
        "predeterminado",
        "activo",
        "fecha_creacion",
    )

    list_filter = (
        "tipo",
        "marca",
        "predeterminado",
        "activo",
    )

    search_fields = (
        "cliente__nombre_razon_social",
        "cliente__documento",
        "titular",
        "ultimos_cuatro",
        "alias",
    )

    readonly_fields = (
        "fecha_creacion",
        "fecha_modificacion",
    )

    ordering = (
        "-predeterminado",
        "-fecha_creacion",
    )