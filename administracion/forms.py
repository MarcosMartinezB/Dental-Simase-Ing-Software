from django import forms

from citas.models import TipoAtencion


class TipoAtencionForm(forms.ModelForm):
    class Meta:
        model = TipoAtencion
        fields = ['nombre', 'costo', 'duracion_minutos', 'activo']
        labels = {
            'nombre': 'Nombre de la atención',
            'costo': 'Valor ($)',
            'duracion_minutos': 'Duración (minutos)',
            'activo': 'Vigente',
        }
        help_texts = {
            'costo': 'Las atenciones ya registradas conservan el valor con que se realizaron.',
            'duracion_minutos': 'Tiempo que se reserva en la agenda (entre 10 y 240).',
            'activo': 'Si se desmarca, deja de ofrecerse en nuevas citas y atenciones.',
        }

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        repetido = TipoAtencion.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk)
        if repetido.exists():
            raise forms.ValidationError('Ya existe una atención con ese nombre.')
        return nombre
