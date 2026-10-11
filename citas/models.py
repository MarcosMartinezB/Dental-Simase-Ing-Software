from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class TipoAtencion(models.Model):
    """Catálogo de atenciones: define el valor y la duración de cada una."""
    nombre = models.CharField(max_length=100, unique=True)
    costo = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    duracion_minutos = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(10), MaxValueValidator(240)],
        help_text='Tiempo que se reserva en la agenda.',
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tipo de atención"
        verbose_name_plural = "Tipos de atención"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.duracion_minutos} min)"


class EstadoCita(models.TextChoices):
    RESERVADA = 'RESERVADA', 'Reservada'
    CONFIRMADA = 'CONFIRMADA', 'Confirmada'
    EN_ATENCION = 'EN_ATENCION', 'En atención'
    COMPLETADA = 'COMPLETADA', 'Completada'
    CANCELADA = 'CANCELADA', 'Cancelada'


class Cita(models.Model):
    paciente = models.ForeignKey(
        'usuarios.Paciente', on_delete=models.PROTECT, related_name='citas'
    )
    odontologo = models.ForeignKey(
        'usuarios.Odontologo', on_delete=models.PROTECT, related_name='citas'
    )
    tipo_atencion = models.ForeignKey(
        TipoAtencion, on_delete=models.PROTECT, related_name='citas'
    )
    fecha_hora = models.DateTimeField()
    # Se calcula sola con la duración del tipo de atención (se guarda para
    # poder detectar cruces de horario con una consulta a la base de datos).
    fecha_hora_fin = models.DateTimeField(null=True, blank=True, editable=False)
    estado = models.CharField(
        max_length=20, choices=EstadoCita.choices, default=EstadoCita.RESERVADA
    )

    class Meta:
        ordering = ['fecha_hora']

    def _fin_calculado(self):
        return self.fecha_hora + timedelta(minutes=self.tipo_atencion.duracion_minutos)

    def clean(self):
        if not (self.odontologo_id and self.tipo_atencion_id and self.fecha_hora):
            return
        if self.estado == EstadoCita.CANCELADA:
            return

        inicio, fin = self.fecha_hora, self._fin_calculado()

        if self._state.adding:
            if inicio < timezone.now():
                raise ValidationError('No se puede reservar una cita en el pasado.')
            if not self.tipo_atencion.activo:
                raise ValidationError('Ese tipo de atención ya no está disponible.')

        # Dos citas se cruzan si una empieza antes de que la otra termine.
        vigentes = (
            Cita.objects
            .filter(fecha_hora__lt=fin, fecha_hora_fin__gt=inicio)
            .exclude(estado=EstadoCita.CANCELADA)
            .exclude(pk=self.pk)
        )
        if vigentes.filter(odontologo_id=self.odontologo_id).exists():
            raise ValidationError('El odontólogo ya tiene una cita que se cruza con ese horario.')
        if self.paciente_id and vigentes.filter(paciente_id=self.paciente_id).exists():
            raise ValidationError('El paciente ya tiene otra cita en ese horario.')

    def save(self, *args, **kwargs):
        if self.fecha_hora and self.tipo_atencion_id:
            self.fecha_hora_fin = self._fin_calculado()
        super().save(*args, **kwargs)

    def confirmar(self):
        if self.estado != EstadoCita.RESERVADA:
            raise ValidationError('Solo se puede confirmar una cita reservada.')
        self.estado = EstadoCita.CONFIRMADA
        self.save(update_fields=['estado'])

    def cancelar(self):
        if self.estado in (EstadoCita.COMPLETADA, EstadoCita.CANCELADA):
            raise ValidationError('Esta cita ya no se puede cancelar.')
        self.estado = EstadoCita.CANCELADA
        self.save(update_fields=['estado'])

    def __str__(self):
        return f"{self.fecha_hora:%d/%m/%Y %H:%M} - {self.paciente} con {self.odontologo}"
