from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("divisas", "0002_seed_pyg"),
        ("transacciones", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaccion",
            name="cantidad_divisa",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=14,
                null=True,
                validators=[django.core.validators.MinValueValidator(0.01)],
                verbose_name="Cantidad en divisa",
            ),
        ),
        migrations.AddField(
            model_name="transaccion",
            name="divisa",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="transacciones_extranjeras",
                to="divisas.moneda",
                verbose_name="Divisa operada",
            ),
        ),
        migrations.AddField(
            model_name="transaccion",
            name="fecha_finalizacion",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Fecha de finalización",
            ),
        ),
        migrations.AddField(
            model_name="transaccion",
            name="tipo_operacion",
            field=models.CharField(
                blank=True,
                choices=[("compra", "Compra"), ("venta", "Venta")],
                max_length=6,
                null=True,
                verbose_name="Tipo de operación",
            ),
        ),
    ]