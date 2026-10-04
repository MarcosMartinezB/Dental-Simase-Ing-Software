from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone


class EstadoPago(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    APROBADO = 'APROBADO', 'Aprobado'
    RECHAZADO = 'RECHAZADO', 'Rechazado'


class MedioPago(models.TextChoices):
    EFECTIVO = 'EFECTIVO', 'Efectivo'
    TARJETA_PRESENCIAL = 'TARJETA_PRESENCIAL', 'Tarjeta presencial (POS)'
    # TARJETA_ONLINE se agregará con la integración futura de Webpay Plus.


class ResultadoPOS(models.TextChoices):
    APROBADO = 'APROBADO', 'Aprobado en el POS'
    RECHAZADO = 'RECHAZADO', 'Rechazado en el POS'


class Pago(models.Model):
    """Context del patrón Strategy: delega el procesamiento en una EstrategiaPago."""
    cita = models.OneToOneField(
        'citas.Cita', on_delete=models.PROTECT, related_name='pago'
    )
    monto = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))]
    )
    fecha_pago = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(
        max_length=10, choices=EstadoPago.choices, default=EstadoPago.PENDIENTE
    )

    # Datos que usa la estrategia elegida (según el medio, solo algunos aplican).
    medio = models.CharField(max_length=20, choices=MedioPago.choices)
    monto_recibido = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    referencia_pos = models.CharField(max_length=50, blank=True)
    resultado_pos = models.CharField(
        max_length=10, choices=ResultadoPOS.choices, blank=True
    )

    class Meta:
        ordering = ['-fecha_pago']

    # --- Strategy ---------------------------------------------------------
    @property
    def estrategia(self):
        """Estrategia elegida; si el objeto viene de la BD, se reconstruye desde sus campos."""
        elegida = getattr(self, '_estrategia', None)
        if elegida is not None:
            return elegida
        from .estrategias import PagoEfectivo, PagoTarjetaPresencial
        if self.medio == MedioPago.EFECTIVO:
            return PagoEfectivo(self.monto_recibido or Decimal('0'))
        if self.medio == MedioPago.TARJETA_PRESENCIAL:
            return PagoTarjetaPresencial(self.referencia_pos, self.resultado_pos)
        return None

    def seleccionar_estrategia(self, estrategia):
        self._estrategia = estrategia
        self.medio = estrategia.medio
        # Limpia datos de un intento anterior con otro medio y copia los nuevos.
        self.monto_recibido = None
        self.referencia_pos = ''
        self.resultado_pos = ''
        for campo, valor in estrategia.datos().items():
            setattr(self, campo, valor)

    def procesar(self):
        if self.estado == EstadoPago.APROBADO:
            raise ValidationError('Este pago ya fue aprobado.')
        estrategia = self.estrategia
        if estrategia is None:
            raise ValidationError('Debe seleccionar un medio de pago.')
        with transaction.atomic():
            self.estado = estrategia.procesar_pago(self.monto)
            self.fecha_pago = timezone.now()
            self.save()
            if self.estado == EstadoPago.APROBADO:
                ComprobantePago(pago=self).generar()  # solo los aprobados
        return self.estado

    # --- Validaciones -----------------------------------------------------
    def clean(self):
        if not self.medio:
            raise ValidationError({'medio': 'Seleccione el medio de pago.'})
        if self.medio == MedioPago.EFECTIVO and self.monto_recibido is None:
            raise ValidationError({'monto_recibido': 'Indique el monto recibido en efectivo.'})
        if self.medio == MedioPago.TARJETA_PRESENCIAL:
            if not self.referencia_pos:
                raise ValidationError({'referencia_pos': 'Ingrese la referencia del POS.'})
            if not self.resultado_pos:
                raise ValidationError({'resultado_pos': 'Indique el resultado del POS.'})

    def __str__(self):
        return f"Pago {self.pk} - {self.get_estado_display()} (${self.monto})"


class ComprobantePago(models.Model):
    pago = models.OneToOneField(
        Pago, on_delete=models.PROTECT, related_name='comprobante'
    )
    numero = models.CharField(max_length=20, unique=True, blank=True)
    fecha_emision = models.DateTimeField(default=timezone.now)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Comprobante de pago"
        verbose_name_plural = "Comprobantes de pago"

    def generar(self):
        """Emite el comprobante solo para pagos aprobados. Devuelve True si lo generó."""
        if self.pk or self.pago.estado != EstadoPago.APROBADO:
            return False
        self.numero = f"CP-{self.pago_id:06d}"
        self.monto_total = self.pago.monto
        self.save()
        return True

    def __str__(self):
        return self.numero or 'Comprobante sin emitir'