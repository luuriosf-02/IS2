import uuid

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("clientes", "0007_remove_cliente_customer_id"),
        ("divisas", "0002_seed_pyg"),
        ("payments", "0002_mediopago_delete_paymentmethod"),
    ]

    operations = [
        migrations.CreateModel(
            name="Transaccion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "identificador",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                        verbose_name="Identificador",
                    ),
                ),
                (
                    "monto",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=14,
                        validators=[
                            django.core.validators.MinValueValidator(0.01)
                        ],
                        verbose_name="Monto",
                    ),
                ),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("pendiente", "Pendiente"),
                            ("pagada", "Pagada"),
                            ("anulada", "Anulada"),
                            ("cancelada", "Cancelada"),
                        ],
                        default="pendiente",
                        max_length=10,
                        verbose_name="Estado",
                    ),
                ),
                (
                    "referencia",
                    models.CharField(
                        max_length=100,
                        unique=True,
                        verbose_name="Referencia",
                    ),
                ),
                (
                    "descripcion",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="Descripción",
                    ),
                ),
                (
                    "fecha_creacion",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Fecha de creación",
                    ),
                ),
                (
                    "fecha_actualizacion",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="Fecha de actualización",
                    ),
                ),
                (
                    "cliente",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="transacciones",
                        to="clientes.cliente",
                        verbose_name="Cliente",
                    ),
                ),
                (
                    "medio_pago",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="transacciones",
                        to="payments.mediopago",
                        verbose_name="Medio de pago",
                    ),
                ),
                (
                    "moneda",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="transacciones",
                        to="divisas.moneda",
                        verbose_name="Moneda",
                    ),
                ),
            ],
            options={
                "verbose_name": "Transacción",
                "verbose_name_plural": "Transacciones",
                "ordering": ["-fecha_creacion"],
            },
        ),
    ]