# views.py
import stripe
import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.urls import reverse

from apps.payments.models import ClienteStripeCustomer, MedioPago
from apps.users.client_selection import get_selected_client
from apps.stripe.services import save_stripe_payment_method

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


def get_or_create_customer(client, email):
    stripe_customer = ClienteStripeCustomer.objects.filter(cliente=client).first()
    if stripe_customer:
        if email:
            stripe.Customer.modify(
                stripe_customer.stripe_customer_id,
                email=email,
            )
        return stripe_customer.stripe_customer_id

    customer_data = {
        "name": client.nombre_razon_social,
        "metadata": {"cliente_id": str(client.pk)},
    }
    if email:
        customer_data["email"] = email

    customer = stripe.Customer.create(**customer_data)
    stripe_customer = ClienteStripeCustomer.objects.create(
        cliente=client,
        stripe_customer_id=customer.id,
    )
    return stripe_customer.stripe_customer_id


@login_required
@require_POST
def create_checkout_session(request):
    client = get_selected_client(request)
    if client is None or not client.activo:
        return HttpResponse(status=403)

    stage = "crear el cliente"
    try:
        customer_id = get_or_create_customer(client, request.user.email)
        return_url = request.build_absolute_uri(reverse("payments:lista"))
        stage = "crear la sesión de Checkout"
        session = stripe.checkout.Session.create(
            mode="setup",
            currency="usd",
            customer=customer_id,
            success_url=return_url,
            cancel_url=return_url,
        )
    except stripe.error.StripeError as exc:
        user_message = getattr(exc, "user_message", None)
        logger.error(
            "Stripe falló al %s (%s, code=%s, request_id=%s): %s",
            stage,
            type(exc).__name__,
            getattr(exc, "code", None),
            getattr(exc, "request_id", None),
            user_message or str(exc),
        )
        messages.error(
            request,
            user_message or "No se pudo iniciar el registro con Stripe. Revisá los logs del servidor.",
        )
        return redirect("payments:lista")

    return redirect(session.url, code=303)


@login_required
def confirm_delete_payment_method(request, pk):
    client = get_selected_client(request)
    if client is None or not client.activo:
        return HttpResponse(status=403)

    medio_pago = get_object_or_404(
        MedioPago,
        pk=pk,
        cliente=client,
        stripe_payment_method_id__isnull=False,
    )
    return render(request, "payments/confirmar_eliminacion.html", {
        "medio_pago": medio_pago,
    })


@login_required
@require_POST
def delete_payment_method(request, pk):
    client = get_selected_client(request)
    if client is None or not client.activo:
        return HttpResponse(status=403)

    medio_pago = get_object_or_404(
        MedioPago,
        pk=pk,
        cliente=client,
        stripe_payment_method_id__isnull=False,
    )
    try:
        stripe.PaymentMethod.detach(medio_pago.stripe_payment_method_id)
    except stripe.error.StripeError:
        messages.error(request, "Stripe no pudo eliminar el medio de pago.")
    else:
        medio_pago.delete()
        messages.success(request, "El medio de pago fue eliminado en Stripe.")

    return redirect("payments:lista")


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event["type"] == "setup_intent.succeeded":
        setup_intent = event["data"]["object"]
        try:
            stripe_customer = ClienteStripeCustomer.objects.select_related("cliente").get(
                stripe_customer_id=setup_intent["customer"],
            )
        except ClienteStripeCustomer.DoesNotExist:
            return HttpResponse(status=200)
        client = stripe_customer.cliente
        if not client.activo:
            return HttpResponse(status=200)

        payment_method = stripe.PaymentMethod.retrieve(
            setup_intent["payment_method"]
        )
        save_stripe_payment_method(client, payment_method)
    elif event["type"] == "payment_method.detached":
        payment_method = event["data"]["object"]
        MedioPago.objects.filter(
            stripe_payment_method_id=payment_method["id"]
        ).delete()

    return HttpResponse(status=200)