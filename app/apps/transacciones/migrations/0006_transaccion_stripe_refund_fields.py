from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("transacciones", "0005_transaccion_stripe_payment_intent_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaccion",
            name="stripe_refund_id",
            field=models.CharField(
                blank=True,
                max_length=255,
                verbose_name="Reembolso de Stripe",
            ),
        ),
        migrations.AddField(
            model_name="transaccion",
            name="stripe_refund_reason",
            field=models.CharField(
                blank=True,
                max_length=500,
                verbose_name="Motivo del reembolso",
            ),
        ),
    ]