from django import forms

from usuarios.models import Odontologo, Paciente

from .models import Cita, TipoAtencion

FORMATO_FECHA_HORA = '%Y-%m-%dT%H:%M'  # el que entrega <input type="datetime-local">


class CitaPacienteForm(forms.ModelForm):
    """Reserva hecha por el propio paciente: el paciente lo pone la vista."""

    class Meta:
        model = Cita
        fields = ['tipo_atencion', 'odontologo', 'fecha_hora']
        labels = {
            'tipo_atencion': 'Tipo de atención',
            'odontologo': 'Odontólogo',
            'fecha_hora': 'Fecha y hora',
        }
        widgets = {
            'fecha_hora': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format=FORMATO_FECHA_HORA),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_hora'].input_formats = [FORMATO_FECHA_HORA]
        self.fields['tipo_atencion'].queryset = TipoAtencion.objects.filter(activo=True)
        self.fields['odontologo'].queryset = (
            Odontologo.objects.select_related('usuario').filter(usuario__activo=True))
        self.fields['tipo_atencion'].help_text = 'La duración de la cita depende de la atención elegida.'


class CitaRecepcionForm(CitaPacienteForm):
    """Cita presencial: recepción elige además al paciente."""

    class Meta(CitaPacienteForm.Meta):
        fields = ['paciente', 'tipo_atencion', 'odontologo', 'fecha_hora']
        labels = {**CitaPacienteForm.Meta.labels, 'paciente': 'Paciente'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['paciente'].queryset = (
            Paciente.objects.select_related('usuario').filter(usuario__activo=True))