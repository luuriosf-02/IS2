from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0007_remove_cliente_customer_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="email",
            field=models.EmailField(
                blank=True,
                max_length=254,
                verbose_name="Correo para facturación",
            ),
        ),
    ]