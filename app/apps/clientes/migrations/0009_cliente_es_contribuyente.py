from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0008_cliente_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="es_contribuyente",
            field=models.BooleanField(
                blank=True,
                null=True,
                verbose_name="Contribuyente",
            ),
        ),
    ]