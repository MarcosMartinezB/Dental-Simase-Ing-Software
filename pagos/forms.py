from django import forms

from .models import MedioPago, ResultadoPOS


class PagoForm(forms.Form):
    medio = forms.ChoiceField(
        label='Medio de pago',
        choices=[('', 'Selecciona el medio de pago')] + MedioPago.choices)
    monto_recibido = forms.DecimalField(
        label='Monto recibido en efectivo', required=False,
        min_value=0, max_digits=10, decimal_places=2)
    referencia_pos = forms.CharField(
        label='Referencia del POS', required=False, max_length=50)
    resultado_pos = forms.ChoiceField(
        label='Resultado en el POS', required=False,
        choices=[('', 'Selecciona el resultado')] + ResultadoPOS.choices)

    def clean(self):
        d = super().clean()
        medio = d.get('medio')
        if medio == MedioPago.EFECTIVO and d.get('monto_recibido') is None:
            self.add_error('monto_recibido', 'Indica cuánto efectivo se recibió.')
        if medio == MedioPago.TARJETA_PRESENCIAL:
            if not d.get('referencia_pos'):
                self.add_error('referencia_pos', 'Ingresa la referencia que entregó el POS.')
            if not d.get('resultado_pos'):
                self.add_error('resultado_pos', 'Indica el resultado que mostró el POS.')
        return d
