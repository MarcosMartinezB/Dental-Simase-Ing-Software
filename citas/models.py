from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


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
    fecha_hora = models.DateTimeField()
    estado = models.CharField(
        max_length=20, choices=EstadoCita.choices, default=EstadoCita.RESERVADA
    )

    class Meta:
        ordering = ['fecha_hora']

    def clean(self):
        # Verificar disponibilidad: el odontólogo no puede tener dos citas
        # vigentes a la misma hora.
        if self.estado != EstadoCita.CANCELADA and self.odontologo_id and self.fecha_hora:
            choque = (
                Cita.objects
                .filter(odontologo_id=self.odontologo_id, fecha_hora=self.fecha_hora)
                .exclude(estado=EstadoCita.CANCELADA)
                .exclude(pk=self.pk)
                .exists()
            )
            if choque:
                raise ValidationError('El odontólogo ya tiene una cita en ese horario.')
            if self._state.adding and self.fecha_hora < timezone.now():
                raise ValidationError('No se puede reservar una cita en el pasado.')

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