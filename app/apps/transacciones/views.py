import uuid
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.dashboard.views import (
    PYG_CODE,
    calculate_conversion,
    get_currency,
    get_currencies,
)
from apps.divisas.models import Moneda
from apps.payments.models import MedioPago
from apps.users.client_selection import get_selected_client

from .models import Transaccion


@login_required
def crear_transaccion(request):
    if request.method != "POST":
        return redirect("/#conversor")

    cliente = get_selected_client(request)
    if cliente is None or not cliente.activo:
        messages.error(request, "Necesitas un cliente activo para efectuar la operación.")
        return redirect("/#conversor")

    medio_pago = MedioPago.objects.filter(
        pk=request.POST.get("medio_pago"),
        cliente=cliente,
        activo=True,
    ).first()
    if medio_pago is None:
        messages.error(request, "Selecciona un medio de pago activo para continuar.")
        return redirect("/#conversor")

    try:
        amount = Decimal(request.POST.get("amount", ""))
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal("0")

    operation = request.POST.get("operation")
    currency_code = request.POST.get("currency")
    currencies = [currency for currency in get_currencies() if currency["codigo"] != PYG_CODE]
    currency = get_currency(currency_code, currencies)

    if amount <= 0 or operation not in ("compra", "venta") or currency is None:
        messages.error(request, "Los datos de la operación ya no son válidos. Vuelve a calcularla.")
        return redirect("/#conversor")

    conversion = calculate_conversion(amount, operation, currency)
    moneda_pyg = Moneda.objects.filter(codigo=PYG_CODE, activa=True).first()
    if moneda_pyg is None:
        messages.error(request, "La moneda de liquidación no está disponible.")
        return redirect("/#conversor")

    Transaccion.objects.create(
        cliente=cliente,
        medio_pago=medio_pago,
        monto=conversion["result"],
        moneda=moneda_pyg,
        cantidad_divisa=conversion["amount"],
        divisa=Moneda.objects.get(codigo=conversion["foreign_currency"]),
        tipo_operacion=operation,
        estado=Transaccion.ESTADO_PENDIENTE,
        referencia=f"GE-{uuid.uuid4().hex[:12].upper()}",
        descripcion=(
            f"{operation.capitalize()} de {conversion['amount']} "
            f"{conversion['foreign_currency']}"
        ),
    )
    messages.success(request, "La operación fue registrada y quedó pendiente de pago.")
    return redirect("/#conversor")


@login_required
def historial_transacciones(request):
    cliente = get_selected_client(request)
    if cliente is None or not cliente.activo:
        messages.error(request, "Necesitas un cliente activo para consultar el historial.")
        return redirect("home")

    transacciones = (
        Transaccion.objects
        .filter(cliente=cliente)
        .select_related("medio_pago", "moneda", "divisa")
    )
    return render(
        request,
        "transacciones/historial.html",
        {
            "cliente": cliente,
            "transacciones": transacciones,
        },
    )