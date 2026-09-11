from django.db import models

from apps.clientes.models import Cliente


class MedioPago(models.Model):
    """
    Representa un medio de pago registrado por un cliente.

    Almacena datos identificativos como el tipo, la marca,
    los últimos cuatro dígitos y el vencimiento. No almacena
    el número completo de la tarjeta ni el código CVV.
    """
    TIPO_CHOICES = [
        ("CREDITO", "Tarjeta de crédito"),
        ("DEBITO", "Tarjeta de débito"),
        ("BILLETERA", "Billetera electrónica"),
    ]

    MARCA_CHOICES = [
        ("VISA", "Visa"),
        ("MASTERCARD", "Mastercard"),
        ("AMEX", "American Express"),
        ("OTRA", "Otra"),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="medios_pago",
        verbose_name="Cliente",
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de medio de pago",
    )

    alias = models.CharField(
        max_length=100,
        verbose_name="Alias",
        help_text="Ejemplo: Tarjeta personal",
    )

    titular = models.CharField(
        max_length=150,
        verbose_name="Nombre del titular",
    )

    marca = models.CharField(
        max_length=20,
        choices=MARCA_CHOICES,
        verbose_name="Marca",
    )

    ultimos_cuatro = models.CharField(
        max_length=4,
        verbose_name="Últimos cuatro dígitos",
    )

    mes_vencimiento = models.PositiveSmallIntegerField(
        verbose_name="Mes de vencimiento",
    )

    anio_vencimiento = models.PositiveSmallIntegerField(
        verbose_name="Año de vencimiento",
    )

    predeterminado = models.BooleanField(
        default=False,
        verbose_name="Medio predeterminado",
    )

    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación",
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de modificación",
    )

    def __str__(self):
        return (
            f"{self.get_marca_display()} "
            f"terminada en {self.ultimos_cuatro}"
        )

    class Meta:
        ordering = ["-predeterminado", "-fecha_creacion"]
        verbose_name = "Medio de pago"
        verbose_name_plural = "Medios de pago"