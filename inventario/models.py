from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone


class TipoMovimiento(models.TextChoices):
    ENTRADA = 'ENTRADA', 'Entrada por compra'
    SALIDA = 'SALIDA', 'Salida a box clínico'


class Insumo(models.Model):
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=100)
    stock_actual = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['nombre']

    def verificar_stock_minimo(self):
        """True si el stock cubre el mínimo; False si está por debajo (requiere reabastecer)."""
        return self.stock_actual >= self.stock_minimo

    def actualizar_stock(self, cantidad):
        """Suma `cantidad` al stock (negativa para salidas). No permite stock negativo."""
        nuevo = self.stock_actual + cantidad
        if nuevo < 0:
            raise ValidationError(
                f'Stock insuficiente de {self.nombre}: hay {self.stock_actual}.'
            )
        self.stock_actual = nuevo
        self.save(update_fields=['stock_actual'])

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class MovimientoInventario(models.Model):
    insumo = models.ForeignKey(
        Insumo, on_delete=models.PROTECT, related_name='movimientos'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='movimientos_inventario'
    )
    atencion = models.ForeignKey(
        'fichas.Atencion', on_delete=models.PROTECT, null=True, blank=True,
        related_name='movimientos_inventario'
    )
    fecha_hora = models.DateTimeField(default=timezone.now)
    tipo = models.CharField(max_length=10, choices=TipoMovimiento.choices)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = "Movimiento de inventario"
        verbose_name_plural = "Movimientos de inventario"
        ordering = ['-fecha_hora']

    def clean(self):
        if self.atencion_id and self.tipo != TipoMovimiento.SALIDA:
            raise ValidationError('Solo una salida puede asociarse a una atención.')
        if (self._state.adding and self.tipo == TipoMovimiento.SALIDA
                and self.insumo_id and self.cantidad
                and self.cantidad > self.insumo.stock_actual):
            raise ValidationError(
                f'La salida ({self.cantidad}) supera el stock disponible '
                f'({self.insumo.stock_actual}).'
            )

    def registrar(self):
        """
        Guarda el movimiento y actualiza el stock en una sola transacción.
        Devuelve False si ya estaba registrado, para no descontar dos veces.
        """
        if not self._state.adding:
            return False
        self.full_clean()
        self._registrando = True
        try:
            with transaction.atomic():
                insumo = Insumo.objects.select_for_update().get(pk=self.insumo_id)
                delta = self.cantidad if self.tipo == TipoMovimiento.ENTRADA else -self.cantidad
                insumo.actualizar_stock(delta)  # falla si queda negativo
                self.save(force_insert=True)
        finally:
            self._registrando = False
        return True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError('Un movimiento registrado no se puede modificar.')
        if not getattr(self, '_registrando', False):
            self.registrar()  # cualquier alta pasa por registrar()
            return
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_tipo_display()} {self.cantidad} x {self.insumo.nombre}"