from django.db import models

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
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre_razon_social} ({self.get_tipo_persona_display()})"