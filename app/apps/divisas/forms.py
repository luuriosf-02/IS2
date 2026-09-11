from django import forms
from .models import Moneda, TasaCambio


class MonedaForm(forms.ModelForm):
    class Meta:
        model = Moneda
        fields = ['codigo', 'nombre', 'simbolo', 'activa']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'USD'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dólar Estadounidense'}),
            'simbolo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '$'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TasaCambioForm(forms.ModelForm):
    class Meta:
        model = TasaCambio
        fields = ['moneda', 'tasa_compra', 'tasa_venta']
        widgets = {
            'moneda': forms.Select(attrs={'class': 'form-select'}),
            'tasa_compra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001', 'placeholder': 'Ej: 7300'}),
            'tasa_venta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001', 'placeholder': 'Ej: 7400'}),
        }