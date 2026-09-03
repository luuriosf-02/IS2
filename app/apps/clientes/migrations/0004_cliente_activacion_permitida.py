from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0003_alter_cliente_activo'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='activacion_permitida',
            field=models.BooleanField(default=False),
        ),
    ]