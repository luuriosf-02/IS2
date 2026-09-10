from django import forms
from .models import TasaCambio

class TasaCambioForm(forms.ModelForm):
    class Meta:
        model = TasaCambio
        fields = '__all__'