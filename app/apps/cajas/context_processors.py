from .services import puede_operar, puede_administrar


def permisos_caja(request):
    admin = puede_administrar(request.user)
    return {
        "puede_operar_caja": puede_operar(request.user) or admin,
        "puede_administrar_cajas": admin,
    }

