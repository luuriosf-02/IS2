from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import TasaCambio, Moneda, Notificacion
from django.urls import path
from apps.divisas.models import Notificacion
from django.contrib.auth.models import User
from django.utils import timezone
from apps.transacciones.models import Transaccion

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
            
            # Notifica a los usuarios sobre la nueva cotización
            Notificacion.objects.create(
                usuario=request.user,
                mensaje=f"Se ha registrado una nueva cotización para {instancia_moneda.nombre}"
            )
            return redirect('gestion_divisas')

    return render(request, 'divisas/gestion_divisas.html')


def dashboard_cliente(request):
    # 1. Obtenemos las tasas vigentes
    tasas_vigentes = TasaCambio.objects.select_related('moneda').all().order_by('moneda')
    
    # 2. Obtenemos las notificaciones del usuario autenticado vía Keycloak
    notificaciones_usuario = Notificacion.objects.filter(usuario=request.user).order_by('-fecha_creacion')[:10]
    notificaciones_no_leidas_count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
    
    # 3. Unificamos todo en un único contexto
    context = {
        'tasas_vigentes': tasas_vigentes,
        'tasas': tasas_vigentes, 
        'notificaciones_usuario': notificaciones_usuario,
        'notificaciones_no_leidas_count': notificaciones_no_leidas_count,
    }

    # 4. Renderizamos el template correcto una sola vez
    return render(request, 'clientes/dashboard_cliente.html', context)


def cancelar_transaccion(request, transaccion_id):
    # Buscamos la transacción
    transaccion = get_object_or_404(Transaccion, id=transaccion_id)
    
    # Solo permitimos cancelar si está pendiente
    if transaccion.estado == 'Pendiente' or transaccion.estado == 'pendiente':
        transaccion.estado = 'Cancelada'  
        transaccion.fecha_finalizacion = timezone.now() # Registra cuándo terminó/se canceló
        transaccion.save()
        
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('gestion_divisas')