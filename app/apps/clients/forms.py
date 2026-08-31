from django import forms

from .models import Client


class UserClientLinkForm(forms.Form):
    clients = forms.ModelMultipleChoiceField(
        queryset=Client.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Clientes",
    )