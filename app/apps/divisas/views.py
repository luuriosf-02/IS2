from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import TasaCambio, Moneda


@login_required
def gestion_divisas_view(request):
    es_analista = (
        request.user.groups.filter(name='Analista Cambiario').exists()
        or request.user.username.lower() == 'analista'
    )

    if not es_analista and not request.user.is_superuser:
        return render(request, '403.html', status=403)

    if request.method == 'POST':
        codigo_moneda = request.POST.get('moneda')
        compra = request.POST.get('compra')
        venta = request.POST.get('venta')

        if codigo_moneda and compra and venta:
            # Obtiene o crea la moneda usando el código enviado (USD, EUR, BRL, ARS, etc.)
            instancia_moneda, _ = Moneda.objects.get_or_create(
                codigo=codigo_moneda,
                defaults={'nombre': codigo_moneda}
            )

            # Guarda la cotización vinculando los campos exactos del modelo TasaCambio
            TasaCambio.objects.create(
                moneda=instancia_moneda,
                tasa_compra=compra,
                tasa_venta=venta,
                usuario_modificador=request.user,
            )
            return redirect('gestion_divisas')

    tasas = TasaCambio.objects.select_related('moneda').all()

    return render(
        request,
        'divisas/gestion_tasas.html',
        {
            'tasas': tasas,
        },
    )