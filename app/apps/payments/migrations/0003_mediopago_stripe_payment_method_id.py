from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0002_mediopago_delete_paymentmethod"),
    ]

    operations = [
        migrations.AddField(
            model_name="mediopago",
            name="stripe_payment_method_id",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                unique=True,
                verbose_name="Identificador del método en Stripe",
            ),
        ),
        migrations.AlterField(
            model_name="mediopago",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("TARJETA", "Tarjeta"),
                    ("CREDITO", "Tarjeta de crédito"),
                    ("DEBITO", "Tarjeta de débito"),
                    ("BILLETERA", "Billetera electrónica"),
                ],
                max_length=20,
                verbose_name="Tipo de medio de pago",
            ),
        ),
        migrations.CreateModel(
            name="ClienteStripeCustomer",
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
                ("stripe_customer_id", models.CharField(max_length=255, unique=True)),
                (
                    "cliente",
                    models.OneToOneField(
                        on_delete=models.CASCADE,
                        related_name="stripe_customer_link",
                        to="clientes.cliente",
                    ),
                ),
            ],
        ),
    ]