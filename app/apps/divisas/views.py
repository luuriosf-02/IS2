from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import MonedaForm, TasaCambioForm
from .models import TasaCambio, Moneda


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
                messages.success(request, 'Tasa de cambio actualizada correctamente.')
                return redirect('gestion_divisas')
            tasa_en_edicion = tasa
        elif action == 'eliminar_tasa':
            tasa_id = request.POST.get('tasa_id')
            tasa = get_object_or_404(TasaCambio, pk=tasa_id)
            tasa.delete()
            messages.success(request, 'Tasa de cambio eliminada correctamente.')
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