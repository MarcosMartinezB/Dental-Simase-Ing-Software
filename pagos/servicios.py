from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from .models import EstadoPago, Pago


def monto_pendiente(cita):
    """
    Lo que se debe cobrar por la cita: la suma de los tratamientos de su atención
    si ya fue atendida; si no, el valor de la atención reservada.
    """
    atencion = getattr(cita, 'atencion', None)
    if atencion is not None:
        total = atencion.tratamientos.aggregate(t=Sum('costo'))['t']
        if total:
            return total
    return cita.tipo_atencion.costo


@transaction.atomic
def registrar_pago(cita, estrategia, monto=None):
    """Registra un pago presencial. Si había un intento rechazado, lo reutiliza."""
    monto = monto if monto is not None else monto_pendiente(cita)
    pago = Pago.objects.filter(cita=cita).first() or Pago(cita=cita)
    if pago.estado == EstadoPago.APROBADO:
        raise ValidationError('La cita ya tiene un pago aprobado.')
    pago.monto = monto
    pago.seleccionar_estrategia(estrategia)
    pago.full_clean()
    pago.procesar()
    return pago
