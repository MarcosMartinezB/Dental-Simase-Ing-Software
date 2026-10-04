from abc import ABC, abstractmethod
from decimal import Decimal

from .models import EstadoPago, MedioPago, ResultadoPOS


class EstrategiaPago(ABC):
    """Interfaz Strategy."""
    medio = None

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
            return EstadoPago.APROBADO
        return EstadoPago.RECHAZADO  # el efectivo no alcanza

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
        if self.referencia_pos and self.resultado_pos == ResultadoPOS.APROBADO:
            return EstadoPago.APROBADO
        return EstadoPago.RECHAZADO

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