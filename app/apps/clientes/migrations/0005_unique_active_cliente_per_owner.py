from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0004_cliente_activacion_permitida'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='cliente',
            constraint=models.UniqueConstraint(
                condition=Q(activo=True, creado_por__isnull=False),
                fields=('creado_por',),
                name='unique_active_cliente_per_owner',
            ),
        ),
    ]