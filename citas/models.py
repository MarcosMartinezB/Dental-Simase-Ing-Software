from django.db import models
from usuarios.models import Usuario
from fichas.models import Paciente
from usuarios.base import SoftDeleteModel

class CitaMedica(SoftDeleteModel):
    ESTADO_CHOICES = [
        ('RESERVADA', 'Reservada'),
        ('CONFIRMADA', 'Confirmada'),
        ('EN_ATENCION', 'En Atención'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, related_name='citas', verbose_name="Paciente")
    odontologo = models.ForeignKey(
        Usuario, 
        on_delete=models.PROTECT, 
        limit_choices_to={'rol__nombre': 'Odontologo'}, 
        related_name='citas_asignadas',
        verbose_name="Odontólogo"
    )
    fecha_hora = models.DateTimeField(verbose_name="Fecha y Hora de la Cita")
    motivo_consulta = models.TextField(verbose_name="Motivo de Consulta")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='RESERVADA', verbose_name="Estado de Cita")

    class Meta:
        verbose_name = "Cita Médica"
        verbose_name_plural = "Citas Médicas"
        ordering = ['fecha_hora']

    def __str__(self):
        return f"Cita: {self.paciente} con Dr(a). {self.odontologo.last_name} ({self.fecha_hora.strftime('%d/%m/%Y %H:%M')})"
