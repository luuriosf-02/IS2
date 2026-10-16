from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from .models import Notificacion

@login_required
@require_GET
def lista(request):
    qs = Notificacion.objects.filter(usuario=request.user)
    return JsonResponse({
        'no_leidas': qs.filter(leida=False).count(),
        'notificaciones': list(qs.order_by('-fecha_creacion', '-pk').values(
            'id', 'titulo', 'mensaje', 'leida', 'fecha_creacion')[:30]),
    })

@login_required
@require_POST
def leer(request, pk):
    aviso = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    Notificacion.objects.filter(pk=aviso.pk, usuario=request.user).update(leida=True)
    return JsonResponse({'ok': True})

@login_required
@require_POST
def leer_todas(request):
    Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
    return JsonResponse({'ok': True})
