from django import forms

from .models import Insumo, MovimientoInventario


class InsumoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f'{obj.codigo} - {obj.nombre} (stock: {obj.stock_actual})'


class InsumoForm(forms.ModelForm):
    """Alta de un insumo. El stock inicial entra como un movimiento de entrada."""
    stock_inicial = forms.IntegerField(
        label='Stock inicial', min_value=0,
        help_text='Unidades que hay hoy. Queda registrado como una entrada.')

    class Meta:
        model = Insumo
        fields = ['codigo', 'nombre', 'stock_minimo']
        labels = {'codigo': 'Código', 'nombre': 'Nombre', 'stock_minimo': 'Stock mínimo'}
        help_texts = {'stock_minimo': 'Bajo esta cantidad el sistema avisa que hay que reabastecer.'}

    field_order = ['codigo', 'nombre', 'stock_inicial', 'stock_minimo']

    def clean_codigo(self):
        return self.cleaned_data['codigo'].strip().upper()


class MovimientoForm(forms.ModelForm):
    """Entrada por compra o salida a box. No tiene ningún campo de costo."""
    insumo = InsumoChoiceField(queryset=Insumo.objects.all(), empty_label='Selecciona un insumo')

    class Meta:
        model = MovimientoInventario
        fields = ['insumo', 'tipo', 'cantidad']
        labels = {'tipo': 'Tipo de movimiento', 'cantidad': 'Cantidad'}
