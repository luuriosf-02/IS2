from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0002_cliente_creado_por'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cliente',
            name='activo',
            field=models.BooleanField(default=False),
        ),
    ]