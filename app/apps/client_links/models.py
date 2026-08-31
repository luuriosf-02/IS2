from django.conf import settings
from django.db import models


class Client(models.Model):
    name = models.CharField(max_length=150)
    document_number = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name


class UserClientLink(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pendiente"),
        ("APPROVED", "Aprobada"),
        ("REJECTED", "Rechazada"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="client_links",
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="user_links",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDING",
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "client"],
                name="unique_user_client_link",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.client}"