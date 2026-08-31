from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_razon_social', 'documento', 'tipo_persona', 'categoria', 'activo', 'fecha_creacion')
    list_filter = ('tipo_persona', 'categoria', 'activo', 'fecha_creacion')
    search_fields = ('nombre_razon_social', 'documento')
    readonly_fields = ('fecha_creacion',)
    fieldsets = (
        ('Información Principal', {
            'fields': ('nombre_razon_social', 'documento', 'tipo_persona')
        }),
        ('Categorización y Límite', {
            'fields': ('categoria', 'limite_credito')
        }),
        ('Estado', {
            'fields': ('activo', 'fecha_creacion')
        }),
    )
