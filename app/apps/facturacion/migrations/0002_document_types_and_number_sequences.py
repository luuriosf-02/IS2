from django.db import migrations, models
import django.db.models.deletion


def create_document_sequences(apps, schema_editor):
    SecuenciaDocumento = apps.get_model("facturacion", "SecuenciaDocumento")
    SecuenciaDocumento.objects.using(schema_editor.connection.alias).bulk_create(
        [
            SecuenciaDocumento(tipo_documento="factura", siguiente_numero=285),
            SecuenciaDocumento(tipo_documento="nota_credito", siguiente_numero=97),
        ]
    )


def remove_document_sequences(apps, schema_editor):
    SecuenciaDocumento = apps.get_model("facturacion", "SecuenciaDocumento")
    SecuenciaDocumento.objects.using(schema_editor.connection.alias).all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("facturacion", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="facturaelectronica",
            name="tipo_documento",
            field=models.CharField(
                choices=[("factura", "Factura"), ("nota_credito", "Nota de crédito")],
                default="factura",
                max_length=12,
            ),
        ),
        migrations.AlterField(
            model_name="facturaelectronica",
            name="transaccion",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="documentos_electronicos",
                to="transacciones.transaccion",
            ),
        ),
        migrations.CreateModel(
            name="SecuenciaDocumento",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "tipo_documento",
                    models.CharField(
                        choices=[("factura", "Factura"), ("nota_credito", "Nota de crédito")],
                        max_length=12,
                        unique=True,
                    ),
                ),
                ("siguiente_numero", models.PositiveIntegerField()),
            ],
        ),
        migrations.RunPython(create_document_sequences, remove_document_sequences),
        migrations.AddConstraint(
            model_name="facturaelectronica",
            constraint=models.UniqueConstraint(
                fields=("transaccion", "tipo_documento"),
                name="unique_transaction_electronic_document_type",
            ),
        ),
    ]