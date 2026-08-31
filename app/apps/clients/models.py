from django.db import models


class Client(models.Model):
    PERSON_TYPE_CHOICES = [
        ("PHYSICAL", "Persona Física"),
        ("LEGAL", "Persona Jurídica"),
    ]

    CATEGORY_CHOICES = [
        ("RETAIL", "Minorista"),
        ("CORPORATE", "Corporativo"),
        ("VIP", "VIP"),
    ]

    name = models.CharField(
        max_length=150,
        verbose_name="Nombre o razón social",
    )

    document_number = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Número de documento",
    )

    person_type = models.CharField(
        max_length=10,
        choices=PERSON_TYPE_CHOICES,
        verbose_name="Tipo de persona",
    )

    category = models.CharField(
        max_length=10,
        choices=CATEGORY_CHOICES,
        default="RETAIL",
        verbose_name="Categoría",
    )

    is_verified = models.BooleanField(
        default=False,
        verbose_name="Cliente verificado",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )

    def __str__(self):
        return f"{self.name} - {self.document_number}"

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["name"]