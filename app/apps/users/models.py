from django.conf import settings
from django.db import models

from django.contrib.auth.models import User

from apps.clients.models import Client


class UserClientLink(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"
    STATUS_REVOKED = "REVOKED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pendiente"),
        (STATUS_APPROVED, "Aprobada"),
        (STATUS_REJECTED, "Rechazada"),
        (STATUS_REVOKED, "Revocada"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="client_links",
        verbose_name="Usuario",
    )

    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name="user_links",
        verbose_name="Cliente",
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="Estado",
    )

    requested_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de solicitud",
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de revisión",
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reviewed_client_links",
        verbose_name="Revisado por",
    )

    rejection_reason = models.TextField(
        blank=True,
        verbose_name="Motivo del rechazo",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "client"],
                name="unique_user_client_link",
            )
        ]

        ordering = ["-requested_at"]
        verbose_name = "Vinculación usuario-cliente"
        verbose_name_plural = "Vinculaciones usuario-cliente"

    def __str__(self):
        return f"{self.user.username} - {self.client.name}"


class Profile(models.Model):
    # Relación uno a uno con el usuario nativo de Django
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Campo para guardar el rol que viene de OIDC
    role = models.CharField(max_length=50, default='Cliente')
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"