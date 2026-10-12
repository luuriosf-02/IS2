import uuid
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render  
from django.utils import timezone  

from apps.dashboard.views import (
    PYG_CODE,
    calculate_conversion,
    get_currencies,
    get_currency,
)
from apps.divisas.models import Moneda
from apps.payments.models import MedioPago
from apps.users.client_selection import get_selected_client

from .models import Transaccion




@login_required
def cancelar_transaccion(request, transaccion_id):
   
    transaccion = get_object_or_404(Transaccion, id=transaccion_id)
    
    
    if transaccion.estado == 'Pendiente' or transaccion.estado == 'pendiente':
        transaccion.estado = 'Cancelada'  
        transaccion.fecha_finalizacion = timezone.now() 
        transaccion.save()
        
    return redirect('historial_transacciones') 


@login_required
def crear_transaccion(request):
    if request.method != "POST":
        return redirect("/#conversor")

    cliente = get_selected_client(request)
    if cliente is None or not cliente.activo:
        messages.error(request, "Necesitas un cliente activo para efectuar la operación.")
        return redirect("/#conversor")

    destino = (
        "transacciones:historial"
        if request.POST.get("return_to") == "historial"
        else "/#conversor"
    )
    transaccion_id = request.POST.get("transaccion_id")
    accion = request.POST.get("accion")

    if transaccion_id:
        medio_pago = MedioPago.objects.filter(
            pk=request.POST.get("medio_pago"),
            cliente=cliente,
            activo=True,
        ).first()
        if medio_pago is None:
            messages.error(request, "Selecciona un medio de pago activo para continuar.")
            return redirect(destino)

        actualizadas = Transaccion.objects.filter(
            pk=transaccion_id,
            cliente=cliente,
            estado=Transaccion.ESTADO_PENDIENTE,
            medio_pago__isnull=True,
        ).update(
            medio_pago=medio_pago,
            estado=Transaccion.ESTADO_PAGADA,
            fecha_finalizacion=timezone.now(),
        )
        if not actualizadas:
            messages.error(
                request,
                "La operación ya no está pendiente. Vuelve a calcularla con la tasa actual.",
            )
            return redirect(destino)

        messages.success(request, "La operación fue registrada y finalizada correctamente.")
        return redirect(destino)

    if accion not in ("guardar_pendiente", "efectuar"):
        messages.error(request, "Selecciona cómo deseas guardar la operación.")
        return redirect(destino)

    if accion == "efectuar":
        medio_pago = MedioPago.objects.filter(
            pk=request.POST.get("medio_pago"),
            cliente=cliente,
            activo=True,
        ).first()
        if medio_pago is None:
            messages.error(request, "Selecciona un medio de pago activo para efectuar la operación.")
            return redirect(destino)
    else:
        medio_pago = None

    try:
        amount = Decimal(request.POST.get("amount", ""))
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal("0")

    operation = request.POST.get("operation")
    currencies = [currency for currency in get_currencies() if currency["codigo"] != PYG_CODE]
    currency = get_currency(request.POST.get("currency"), currencies)
    if amount <= 0 or operation not in ("compra", "venta") or currency is None:
        messages.error(request, "Los datos de la operación ya no son válidos. Vuelve a calcularla.")
        return redirect(destino)

    conversion = calculate_conversion(amount, operation, currency)
    try:
        quoted_rate = Decimal(request.POST.get("quoted_rate", ""))
    except (InvalidOperation, TypeError, ValueError):
        quoted_rate = None
    if quoted_rate != conversion["rate"]:
        messages.error(request, "La tasa cambió mientras confirmabas. Vuelve a calcular la operación.")
        return redirect(destino)

    moneda_pyg = Moneda.objects.filter(codigo=PYG_CODE, activa=True).first()
    divisa = Moneda.objects.filter(codigo=conversion["foreign_currency"], activa=True).first()
    if moneda_pyg is None or divisa is None:
        messages.error(request, "La moneda de la operación ya no está disponible.")
        return redirect(destino)

    finalizada = accion == "efectuar"
    Transaccion.objects.create(
        cliente=cliente,
        medio_pago=medio_pago,
        monto=conversion["result"],
        moneda=moneda_pyg,
        cantidad_divisa=conversion["amount"],
        divisa=divisa,
        tipo_operacion=operation,
        estado=(
            Transaccion.ESTADO_PAGADA
            if finalizada
            else Transaccion.ESTADO_PENDIENTE
        ),
        referencia=f"GE-{uuid.uuid4().hex[:12].upper()}",
        descripcion=(
            f"{operation.capitalize()} de {conversion['amount']} "
            f"{conversion['foreign_currency']}"
        ),
        fecha_finalizacion=timezone.now() if finalizada else None,
    )

    if finalizada:
        messages.success(request, "La operación fue registrada y finalizada correctamente.")
    else:
        messages.success(request, "La operación se guardó como pendiente de pago.")
    return redirect(destino)


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
    sin_pago = transacciones.filter(
        estado__in=(Transaccion.ESTADO_PENDIENTE, Transaccion.ESTADO_CANCELADA)
    )
    finalizadas = transacciones.exclude(
        estado__in=(Transaccion.ESTADO_PENDIENTE, Transaccion.ESTADO_CANCELADA)
    )
    return render(
        request,
        "transacciones/historial.html",
        {
            "cliente": cliente,
            "transacciones_finalizadas": finalizadas,
            "transacciones_sin_pago": sin_pago,
            "medios_pago": MedioPago.objects.filter(cliente=cliente, activo=True),
        },
    )