from .services import puede_operar

def permisos_caja(request):
    return {'puede_operar_caja': puede_operar(request.user)}
