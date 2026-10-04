from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from .models import EstadoPago, Pago


def monto_pendiente(cita):
    """Suma el costo de los tratamientos de la atención de la cita (0 si no hay)."""
    atencion = getattr(cita, 'atencion', None)
    if atencion is None:
        return Decimal('0')
    return atencion.tratamientos.aggregate(t=Sum('costo'))['t'] or Decimal('0')


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