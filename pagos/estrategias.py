from abc import ABC, abstractmethod
from decimal import Decimal

from .models import EstadoPago, MedioPago, ResultadoPOS


def _clp(valor):
    return '$' + f'{Decimal(valor):,.0f}'.replace(',', '.')


class EstrategiaPago(ABC):
    """Interfaz Strategy. Si rechaza, deja el motivo en `self.motivo`."""
    medio = None
    motivo = ''

    @abstractmethod
    def procesar_pago(self, monto):
        """Devuelve el EstadoPago resultante."""

    def datos(self):
        """Campos de Pago que esta estrategia necesita guardar."""
        return {}


class PagoEfectivo(EstrategiaPago):
    medio = MedioPago.EFECTIVO

    def __init__(self, monto_recibido):
        self.monto_recibido = Decimal(monto_recibido)

    def procesar_pago(self, monto):
        if self.monto_recibido >= monto:
            self.motivo = ''
            return EstadoPago.APROBADO
        self.motivo = (f'El monto recibido ({_clp(self.monto_recibido)}) '
                       f'no cubre el total ({_clp(monto)}).')
        return EstadoPago.RECHAZADO

    def calcular_vuelto(self, monto):
        return max(self.monto_recibido - monto, Decimal('0'))

    def datos(self):
        return {'monto_recibido': self.monto_recibido}


class PagoTarjetaPresencial(EstrategiaPago):
    """El cobro ya ocurrió en el POS: aquí solo se valida y registra su resultado."""
    medio = MedioPago.TARJETA_PRESENCIAL

    def __init__(self, referencia_pos, resultado_pos):
        self.referencia_pos = referencia_pos
        self.resultado_pos = resultado_pos

    def procesar_pago(self, monto):
        # No se hace un segundo cobro ni hay conexión con el terminal.
        if not self.referencia_pos:
            self.motivo = 'Falta la referencia entregada por el POS.'
            return EstadoPago.RECHAZADO
        if self.resultado_pos != ResultadoPOS.APROBADO:
            self.motivo = 'El POS informó que la operación fue rechazada.'
            return EstadoPago.RECHAZADO
        self.motivo = ''
        return EstadoPago.APROBADO

    def datos(self):
        return {'referencia_pos': self.referencia_pos,
                'resultado_pos': self.resultado_pos}


class PagoTarjetaOnline(EstrategiaPago):
    """FUTURO: integración con Webpay Plus. Fuera del prototipo actual."""
    medio = None

    def __init__(self, orden_compra='', token_webpay=''):
        self.orden_compra = orden_compra
        self.token_webpay = token_webpay

    def procesar_pago(self, monto):
        raise NotImplementedError('Integración con Webpay Plus prevista para una etapa futura.')

    def confirmar_pago(self, token):
        raise NotImplementedError('Integración con Webpay Plus prevista para una etapa futura.')
