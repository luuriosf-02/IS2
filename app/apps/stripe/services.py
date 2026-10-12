import stripe

from apps.payments.models import ClienteStripeCustomer, MedioPago


def save_stripe_payment_method(client, payment_method):
    payment_method_data = payment_method.to_dict()
    card = payment_method_data.get("card") or {}
    if not card:
        return None

    brand_name = str(card.get("brand", "")).upper()
    brand = {
        "VISA": "VISA",
        "MASTERCARD": "MASTERCARD",
        "AMERICAN EXPRESS": "AMEX",
        "AMEX": "AMEX",
    }.get(brand_name, "OTRA")
    billing_details = payment_method_data.get("billing_details") or {}
    return MedioPago.objects.update_or_create(
        stripe_payment_method_id=payment_method_data["id"],
        defaults={
            "cliente": client,
            "tipo": "TARJETA",
            "alias": f"{card.get('brand', 'Tarjeta')} **** {card.get('last4', '')}",
            "titular": (
                billing_details.get("name") or client.nombre_razon_social
            )[:150],
            "marca": brand,
            "ultimos_cuatro": card.get("last4", ""),
            "mes_vencimiento": card.get("exp_month"),
            "anio_vencimiento": card.get("exp_year"),
        },
    )[0]


def sync_customer_payment_methods(client):
    stripe_customer = ClienteStripeCustomer.objects.filter(cliente=client).first()
    if stripe_customer is None:
        return

    payment_methods = stripe.PaymentMethod.list(
        customer=stripe_customer.stripe_customer_id,
        type="card",
        limit=100,
    )
    stripe_payment_method_ids = []
    for payment_method in payment_methods.auto_paging_iter():
        medio_pago = save_stripe_payment_method(client, payment_method)
        if medio_pago:
            stripe_payment_method_ids.append(medio_pago.stripe_payment_method_id)

    local_methods = MedioPago.objects.filter(
        cliente=client,
        stripe_payment_method_id__isnull=False,
    )
    if stripe_payment_method_ids:
        local_methods.exclude(
            stripe_payment_method_id__in=stripe_payment_method_ids
        ).delete()
    else:
        local_methods.delete()