from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum


class FichaClinica(models.Model):
    paciente = models.OneToOneField(
        'usuarios.Paciente', on_delete=models.PROTECT, related_name='ficha_clinica'
    )
    fecha_creacion = models.DateField(auto_now_add=True)
    antecedentes_medicos = models.TextField(blank=True)

    class Meta:
        verbose_name = "Ficha clínica"
        verbose_name_plural = "Fichas clínicas"

    def actualizar_antecedentes(self, texto):
        self.antecedentes_medicos = texto
        self.save(update_fields=['antecedentes_medicos'])

    def __str__(self):
        return f"Ficha de {self.paciente}"


class Atencion(models.Model):
    ficha = models.ForeignKey(
        FichaClinica, on_delete=models.PROTECT, related_name='atenciones'
    )
    cita = models.OneToOneField(
        'citas.Cita', on_delete=models.PROTECT, related_name='atencion'
    )
    fecha_hora = models.DateTimeField()
    diagnostico = models.TextField(blank=True)

    class Meta:
        verbose_name = "Atención"
        verbose_name_plural = "Atenciones"
        ordering = ['-fecha_hora']

    def clean(self):
        # La atención debe quedar en la ficha del mismo paciente de la cita.
        if self.ficha_id and self.cita_id:
            if self.ficha.paciente_id != self.cita.paciente_id:
                raise ValidationError(
                    'La ficha clínica no corresponde al paciente de la cita.'
                )

    def registrar_diagnostico(self, texto):
        self.diagnostico = texto
        self.save(update_fields=['diagnostico'])

    def registrar_insumo(self, insumo, cantidad):
        """Registra la salida de un insumo asociada a esta atención."""
        from inventario.models import MovimientoInventario

        movimiento = MovimientoInventario(
            insumo=insumo,
            tipo='SALIDA',
            cantidad=cantidad,
            usuario=self.cita.odontologo.usuario,
            atencion=self,
        )
        movimiento.registrar()
        return movimiento

    def __str__(self):
        return f"Atención {self.fecha_hora:%d/%m/%Y %H:%M} - {self.ficha.paciente}"


class Tratamiento(models.Model):
    atencion = models.ForeignKey(
        Atencion, on_delete=models.CASCADE, related_name='tratamientos'
    )
    nombre = models.CharField(max_length=100)
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20)

    def calcular_costo(self):
        return self.costo

    def __str__(self):
        return self.nombre


class Presupuesto(models.Model):
    atencion = models.OneToOneField(
        Atencion, on_delete=models.CASCADE, related_name='presupuesto'
    )
    fecha_emision = models.DateField(auto_now_add=True)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def calcular_total(self):
        total = self.atencion.tratamientos.aggregate(t=Sum('costo'))['t'] or Decimal('0')
        self.monto_total = total
        self.save(update_fields=['monto_total'])
        return total

    def __str__(self):
        return f"Presupuesto {self.pk} - {self.atencion}"