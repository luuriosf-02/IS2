from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "document_number",
        "person_type",
        "category",
        "is_verified",
        "is_active",
    )

    list_filter = (
        "person_type",
        "category",
        "is_verified",
        "is_active",
    )

    search_fields = (
        "name",
        "document_number",
    )