# models.py
from django.conf import settings
from django.db import models

class StripeCustomer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255, unique=True)

class SavedPaymentMethod(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_pm_id = models.CharField(max_length=255, unique=True)
    brand = models.CharField(max_length=30)
    last4 = models.CharField(max_length=4)
    exp_month = models.PositiveSmallIntegerField()
    exp_year = models.PositiveSmallIntegerField()