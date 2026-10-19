from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("transacciones", "0003_alter_transaccion_medio_pago"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaccion",
            name="receipt_url",
            field=models.URLField(
                blank=True,
                max_length=500,
                verbose_name="Comprobante de pago",
            ),
        ),
    ]