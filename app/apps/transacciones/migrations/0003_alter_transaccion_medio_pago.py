from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0002_mediopago_delete_paymentmethod"),
        ("transacciones", "0002_transaccion_historial_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaccion",
            name="medio_pago",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="transacciones",
                to="payments.mediopago",
                verbose_name="Medio de pago",
            ),
        ),
    ]