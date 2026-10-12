from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from . import services
from .models import Caja, MovimientoCaja
from .forms import ConteoForm, MovimientoForm, AnulacionForm


def cajero_required(view):
    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        services.autorizar(request.user)
        return view(request, *args, **kwargs)
    return wrapper


@cajero_required
def lista(request):
    cajas = Caja.objects.filter(cajero=request.user)
    return render(request, 'cajas/lista.html', {'caja_abierta': cajas.filter(cierre__isnull=True).first(), 'pagina': Paginator(cajas, 20).get_page(request.GET.get('page'))})


@cajero_required
@require_http_methods(['GET', 'POST'])
def apertura(request):
    form = ConteoForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        try:
            caja = services.abrir_caja(request.user, form.montos(), form.cleaned_data['observacion'])
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, 'Caja abierta.')
            return redirect('cajas:detalle', pk=caja.pk)
    return render(request, 'cajas/form.html', {'form': form, 'titulo': 'Abrir caja: saldos iniciales', 'boton': 'Abrir caja'})


@cajero_required
def detalle(request, pk):
    caja = get_object_or_404(Caja, pk=pk, cajero=request.user)
    movimientos = caja.movimientos.select_related('moneda')
    moneda = request.GET.get('moneda', '')
    if moneda.isdigit():
        movimientos = movimientos.filter(moneda_id=int(moneda))
    tipo = request.GET.get('tipo', '')
    if tipo in dict(MovimientoCaja.TIPOS):
        movimientos = movimientos.filter(tipo=tipo)
    estado = request.GET.get('estado', '')
    if estado in ('vigente', 'anulado'):
        movimientos = movimientos.filter(anulado_en__isnull=estado == 'vigente')
    return render(request, 'cajas/detalle.html', {'caja': caja, 'saldos': caja.saldos.select_related('moneda'), 'pagina': Paginator(movimientos, 25).get_page(request.GET.get('page')), 'filtro_moneda': moneda, 'filtro_tipo': tipo, 'filtro_estado': estado})


@cajero_required
@require_http_methods(['GET', 'POST'])
def movimiento(request, pk):
    caja = get_object_or_404(Caja, pk=pk, cajero=request.user)
    if caja.cierre:
        messages.error(request, 'La caja está cerrada.')
        return redirect('cajas:detalle', pk=pk)
    form = MovimientoForm(request.POST if request.method == 'POST' else None, caja=caja)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        try:
            services.registrar_movimiento(request.user, pk, d['moneda'].pk, d['tipo'], d['monto'], d['concepto'], d['clave'], d['referencia'])
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, 'Movimiento registrado.')
            return redirect('cajas:detalle', pk=pk)
    return render(request, 'cajas/form.html', {'form': form, 'titulo': 'Registrar movimiento de efectivo', 'boton': 'Guardar'})


@cajero_required
@require_http_methods(['GET', 'POST'])
def anulacion(request, pk):
    mov = get_object_or_404(MovimientoCaja, pk=pk, caja__cajero=request.user)
    form = AnulacionForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        try:
            services.anular_movimiento(request.user, pk, form.cleaned_data['motivo'])
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, 'Movimiento anulado; saldo revertido.')
            return redirect('cajas:detalle', pk=mov.caja_id)
    return render(request, 'cajas/form.html', {'form': form, 'titulo': f'Anular movimiento #{mov.pk}: {mov.monto} {mov.moneda.codigo}', 'boton': 'Anular movimiento'})


@cajero_required
@require_http_methods(['GET', 'POST'])
def cierre(request, pk):
    caja = get_object_or_404(Caja, pk=pk, cajero=request.user)
    if caja.cierre:
        return redirect('cajas:detalle', pk=pk)
    form = ConteoForm(request.POST if request.method == 'POST' else None, caja=caja)
    if request.method == 'POST' and form.is_valid():
        try:
            services.cerrar_caja(request.user, pk, form.montos(), form.cleaned_data['observacion'])
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, 'Caja cerrada. Consultá el resultado del arqueo.')
            return redirect('cajas:detalle', pk=pk)
    return render(request, 'cajas/form.html', {'form': form, 'titulo': 'Cerrar caja: ingresá el efectivo contado por moneda', 'boton': 'Confirmar cierre'})
