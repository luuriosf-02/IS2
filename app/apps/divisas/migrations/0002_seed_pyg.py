from decimal import Decimal

from django.db import migrations


def crear_guarani(apps, schema_editor):
    Moneda = apps.get_model('divisas', 'Moneda')
    TasaCambio = apps.get_model('divisas', 'TasaCambio')

    pyg, _ = Moneda.objects.get_or_create(
        codigo='PYG',
        defaults={
            'nombre': 'Guaraní paraguayo',
            'simbolo': '₲',
            'activa': True,
        },
    )
    TasaCambio.objects.get_or_create(
        moneda=pyg,
        defaults={
            'tasa_compra': Decimal('1.0000'),
            'tasa_venta': Decimal('1.0000'),
        },
    )


def eliminar_guarani(apps, schema_editor):
    Moneda = apps.get_model('divisas', 'Moneda')
    Moneda.objects.filter(codigo='PYG').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('divisas', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_guarani, eliminar_guarani),
    ]