from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("transacciones", "0004_transaccion_receipt_url"),
    ]

    operations = [
        migrations.CreateModel(
            name="FacturaElectronica",
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
                ("numero_documento", models.CharField(max_length=7, unique=True)),
                ("cdc", models.CharField(blank=True, max_length=44)),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("emitiendo", "Emitiendo"),
                            ("emitida", "Emitida"),
                            ("error", "Error"),
                        ],
                        default="emitiendo",
                        max_length=10,
                    ),
                ),
                ("documento", models.JSONField(default=dict)),
                ("respuesta", models.JSONField(default=dict)),
                ("error", models.TextField(blank=True)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_actualizacion", models.DateTimeField(auto_now=True)),
                (
                    "transaccion",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="factura_electronica",
                        to="transacciones.transaccion",
                    ),
                ),
            ],
            options={
                "verbose_name": "Factura electrónica",
                "verbose_name_plural": "Facturas electrónicas",
                "ordering": ["-fecha_creacion"],
            },
        ),
    ]