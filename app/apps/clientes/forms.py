from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    """Formulario para crear y editar clientes."""
    
    class Meta:
        model = Cliente
        fields = ['nombre_razon_social', 'documento', 'tipo_persona', 'categoria', 'limite_credito', 'activo']
        widgets = {
            'nombre_razon_social': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: Juan Pérez o Empresa S.A.',
                'required': True,
            }),
            'documento': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: 12345678 o RUC-123456-1',
                'required': True,
            }),
            'tipo_persona': forms.Select(attrs={
                'class': 'form-select',
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select',
            }),
            'limite_credito': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
                'required': True,
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
            }),
        }
        labels = {
            'nombre_razon_social': 'Nombre o Razón Social *',
            'documento': 'RUC o CI *',
            'tipo_persona': 'Tipo de Persona *',
            'categoria': 'Categoría *',
            'limite_credito': 'Límite de Crédito *',
            'activo': 'Cliente Activo',
        }
        help_texts = {
            'documento': 'El documento debe ser único en el sistema',
            'limite_credito': 'Monto máximo de crédito disponible',
            'activo': 'Marcar si el cliente está activo',
        }

    def clean_documento(self):
        """Validar que el documento sea único."""
        documento = self.cleaned_data.get('documento')
        # Si estamos editando (self.instance.pk existe), excluir el cliente actual
        if self.instance.pk:
            if Cliente.objects.filter(documento=documento).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('Este documento ya está registrado en el sistema.')
        else:
            if Cliente.objects.filter(documento=documento).exists():
                raise forms.ValidationError('Este documento ya está registrado en el sistema.')
        return documento

    def clean_limite_credito(self):
        """Validar que el límite de crédito sea positivo."""
        limite = self.cleaned_data.get('limite_credito')
        if limite and limite < 0:
            raise forms.ValidationError('El límite de crédito no puede ser negativo.')
        return limite
