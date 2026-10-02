from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .forms import MonedaForm, TasaCambioForm
from .models import TasaCambio, Moneda, Notificacion
from apps.transacciones.models import Transaccion


def _notificar_cotizacion(usuario, moneda):
    Notificacion.objects.create(
        usuario=usuario,
        mensaje=f"Se ha registrado una nueva cotización para {moneda.nombre}"
    )


@login_required
def gestion_divisas_view(request):
    profile = getattr(request.user, 'profile', None)
    es_analista = (
        bool(profile and profile.role == 'Analista Cambiario')
        or request.user.groups.filter(name='Analista Cambiario').exists()
        or request.user.username.lower() == 'analista'
    )

    if not es_analista and not request.user.is_superuser:
        return render(request, '403.html', status=403)

    monedas = Moneda.objects.order_by('codigo')
    tasas = TasaCambio.objects.select_related('moneda').order_by('-fecha_actualizacion')
    tasa_en_edicion = None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'crear_moneda':
            form = MonedaForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Moneda creada correctamente.')
                return redirect('gestion_divisas')
        elif action == 'crear_tasa':
            form = TasaCambioForm(request.POST)
            if form.is_valid():
                tasa = form.save(commit=False)
                tasa.usuario_modificador = request.user
                tasa.save()
                _notificar_cotizacion(request.user, tasa.moneda)
                messages.success(request, 'Tasa de cambio creada correctamente.')
                return redirect('gestion_divisas')
        elif action == 'editar_tasa':
            tasa_id = request.POST.get('tasa_id')
            tasa = get_object_or_404(TasaCambio, pk=tasa_id)
            form = TasaCambioForm(request.POST, instance=tasa)
            if form.is_valid():
                tasa_actualizada = form.save(commit=False)
                tasa_actualizada.usuario_modificador = request.user
                tasa_actualizada.save()
                _notificar_cotizacion(request.user, tasa_actualizada.moneda)
                messages.success(request, 'Tasa de cambio actualizada correctamente.')
                return redirect('gestion_divisas')
            tasa_en_edicion = tasa
        elif action == 'eliminar_tasa':
            tasa_id = request.POST.get('tasa_id')
            tasa = get_object_or_404(TasaCambio, pk=tasa_id)
            tasa.delete()
            messages.success(request, 'Tasa de cambio eliminada correctamente.')
            return redirect('gestion_divisas')
        else:
            # Registro rápido de cotización (flujo nuevo, sin "action")
            codigo_moneda = request.POST.get('moneda')
            compra = request.POST.get('compra')
            venta = request.POST.get('venta')

            if codigo_moneda and compra and venta:
                instancia_moneda, _ = Moneda.objects.get_or_create(
                    codigo=codigo_moneda,
                    defaults={'nombre': codigo_moneda}
                )
                TasaCambio.objects.create(
                    moneda=instancia_moneda,
                    tasa_compra=compra,
                    tasa_venta=venta,
                    usuario_modificador=request.user,
                )
                _notificar_cotizacion(request.user, instancia_moneda)
                return redirect('gestion_divisas')

    edit_tasa_id = request.GET.get('edit_tasa_id')
    if edit_tasa_id:
        tasa_en_edicion = get_object_or_404(TasaCambio, pk=edit_tasa_id)

    moneda_form = MonedaForm()
    tasa_form = TasaCambioForm(instance=tasa_en_edicion) if tasa_en_edicion else TasaCambioForm()

    return render(
        request,
        'divisas/gestion_tasas.html',
        {
            'tasas': tasas,
            'monedas': monedas,
            'moneda_form': moneda_form,
            'tasa_form': tasa_form,
            'tasa_en_edicion': tasa_en_edicion,
        },
    )



def dashboard_cliente(request):
    tasas_vigentes = TasaCambio.objects.select_related('moneda').order_by('moneda')

    notificaciones_usuario = Notificacion.objects.filter(
        usuario=request.user
    ).order_by('-fecha_creacion')[:10]
    notificaciones_no_leidas_count = Notificacion.objects.filter(
        usuario=request.user, leida=False
    ).count()

    context = {
        'tasas_vigentes': tasas_vigentes,
        'tasas': tasas_vigentes,
        'notificaciones_usuario': notificaciones_usuario,
        'notificaciones_no_leidas_count': notificaciones_no_leidas_count,
    }
    return render(request, 'clientes/dashboard_cliente.html', context)


@login_required
def cancelar_transaccion(request, transaccion_id):
    transaccion = get_object_or_404(Transaccion, id=transaccion_id)

    # Solo permitimos cancelar si está pendiente
    if transaccion.estado.lower() == 'pendiente':
        transaccion.estado = 'Cancelada'
        transaccion.fecha_finalizacion = timezone.now()
        transaccion.save()

    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('gestion_divisas')