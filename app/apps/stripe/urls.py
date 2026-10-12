# urls.py
from django.urls import path
from . import views

app_name = "stripe"

urlpatterns = [
    path("payments/checkout/", views.create_checkout_session, name="create_checkout_session"),
    path("payments/<int:pk>/eliminar/confirmar/", views.confirm_delete_payment_method, name="confirm_delete_payment_method"),
    path("payments/<int:pk>/eliminar/", views.delete_payment_method, name="delete_payment_method"),
    path("payments/webhook/", views.stripe_webhook, name="stripe_webhook"),
]