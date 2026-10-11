from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseFormSet, formset_factory

from citas.models import TipoAtencion
from inventario.models import Insumo

from .models import FichaClinica


class AntecedentesForm(forms.ModelForm):
    class Meta:
        model = FichaClinica
        fields = ['antecedentes_medicos']
        labels = {'antecedentes_medicos': 'Antecedentes médicos'}
        help_texts = {'antecedentes_medicos': 'Alergias, enfermedades crónicas, medicamentos en uso.'}
        widgets = {'antecedentes_medicos': forms.Textarea(attrs={'rows': 4})}


class AtencionForm(forms.Form):
    diagnostico = forms.CharField(label='Diagnóstico', widget=forms.Textarea(attrs={'rows': 4}))
    sin_insumos = forms.BooleanField(required=False, label='No se utilizaron insumos')


# --- Atenciones realizadas (el valor sale del catálogo, nunca se digita) -----
class TratamientoForm(forms.Form):
    tipo_atencion = forms.ModelChoiceField(
        queryset=TipoAtencion.objects.filter(activo=True),
        empty_label='Selecciona una atención',
        widget=forms.Select(attrs={'aria-label': 'Tipo de atención'}),
    )


class BaseTratamientoFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return
        if not any(f.cleaned_data for f in self.forms):
            raise ValidationError('Agrega al menos una atención realizada.')


TratamientoFormSet = formset_factory(
    TratamientoForm, formset=BaseTratamientoFormSet, extra=1)


# --- Insumos utilizados --------------------------------------------------------
class InsumoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.nombre} (stock: {obj.stock_actual})'


class InsumoForm(forms.Form):
    insumo = InsumoChoiceField(
        queryset=Insumo.objects.all(), empty_label='Selecciona un insumo',
        widget=forms.Select(attrs={'aria-label': 'Insumo'}))
    cantidad = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'min': 1, 'placeholder': 'Cantidad', 'aria-label': 'Cantidad'}))


InsumoFormSet = formset_factory(InsumoForm, extra=1)