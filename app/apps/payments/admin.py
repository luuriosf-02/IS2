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

    readonly_fields = tuple(field.name for field in MedioPago._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    ordering = (
        "-predeterminado",
        "-fecha_creacion",
    )