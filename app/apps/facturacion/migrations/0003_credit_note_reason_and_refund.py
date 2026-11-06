from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("facturacion", "0002_document_types_and_number_sequences"),
    ]

    operations = [
        migrations.AddField(
            model_name="facturaelectronica",
            name="motivo",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="facturaelectronica",
            name="stripe_refund_id",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]