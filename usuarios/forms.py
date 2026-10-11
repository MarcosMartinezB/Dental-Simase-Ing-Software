from datetime import date

from django import forms

from .models import RolUsuario
from .validators import validar_rut_chileno


class PacienteRegistroForm(forms.Form):
    rut = forms.CharField(label='RUT', max_length=12, validators=[validar_rut_chileno],
                          help_text='Ej.: 12.345.678-5')
    first_name = forms.CharField(label='Nombres', max_length=150)
    last_name = forms.CharField(label='Apellidos', max_length=150)
    email = forms.EmailField(label='Correo electrónico')
    telefono = forms.CharField(label='Teléfono', max_length=15)
    fecha_nacimiento = forms.DateField(
        label='Fecha de nacimiento', widget=forms.DateInput(attrs={'type': 'date'}))

    def clean_fecha_nacimiento(self):
        valor = self.cleaned_data['fecha_nacimiento']
        if valor > date.today():
            raise forms.ValidationError('La fecha de nacimiento no puede ser futura.')
        return valor


class UsuarioInternoForm(forms.Form):
    username = forms.CharField(label='Nombre de usuario', max_length=150)
    first_name = forms.CharField(label='Nombres', max_length=150)
    last_name = forms.CharField(label='Apellidos', max_length=150)
    email = forms.EmailField(label='Correo electrónico')
    especialidad = forms.CharField(label='Especialidad', max_length=100)

    def __init__(self, *args, rol=None, **kwargs):
        super().__init__(*args, **kwargs)
        if rol != RolUsuario.ODONTOLOGO:
            del self.fields['especialidad']  # solo los odontólogos la necesitan
