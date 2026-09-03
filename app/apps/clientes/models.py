from django.db import models
from django.conf import settings
from django.db.models import Q

class Cliente(models.Model):
    """
    Modelo para la gestión y clasificación de clientes.
    Permite registrar clientes como Persona Física o Jurídica 
    y asignarle categorías de segmentación.
    """
    TIPO_PERSONA_CHOICES = [
        ('FISICA', 'Persona Física'),
        ('JURIDICA', 'Persona Jurídica'),
    ]

    CATEGORIA_CHOICES = [
        ('A', 'Categoría A - Premium'),
        ('B', 'Categoría B - Estándar'),
        ('C', 'Categoría C - Riesgo Alto'),
    ]

    nombre_razon_social = models.CharField(max_length=255, verbose_name="Nombre o Razón Social")
    documento = models.CharField(max_length=50, unique=True, verbose_name="RUC o CI")
    tipo_persona = models.CharField(max_length=10, choices=TIPO_PERSONA_CHOICES, default='FISICA')
    categoria = models.CharField(max_length=1, choices=CATEGORIA_CHOICES, default='B')
    limite_credito = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    activo = models.BooleanField(default=False)
    activacion_permitida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='clientes_creados',
        verbose_name='Creado por',
    )

    def __str__(self):
        return f"{self.nombre_razon_social} ({self.get_tipo_persona_display()})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['creado_por'],
                condition=Q(activo=True, creado_por__isnull=False),
                name='unique_active_cliente_per_owner',
            ),
        ]