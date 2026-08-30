from django.shortcuts import render
from .services.keycloak_service import (
    get_users,
    get_roles,
    assign_role_to_user,
)

from .services.keycloak_service import (
    get_users,
    get_roles,
    assign_role_to_user,
)


def assign_role(request):

    context = {}

    try:
        users = get_users()
        roles = get_roles()

        context["users"] = users
        context["roles"] = roles

        if request.method == "POST":

            user_id = request.POST.get("user_id")
            role_name = request.POST.get("role_name")

            if not user_id or not role_name:
                context["error"] = "Debe seleccionar un usuario y un rol."

            else:
                assign_role_to_user(
                    user_id,
                    role_name
                )

                context["message"] = (
                    "Rol asignado correctamente."
                )

    except Exception as e:
        context["error"] = str(e)

    return render(
        request,
        "users/assign_role.html",
        context
    )