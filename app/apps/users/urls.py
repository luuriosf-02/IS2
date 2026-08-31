from django.urls import path
from .views import assign_role

urlpatterns = [
    path(
        "assign-role/",
        assign_role,
        name="assign_role"
    ),
]