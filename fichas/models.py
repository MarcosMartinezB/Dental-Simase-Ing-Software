from django.db import models

from django.db import models
from usuarios.validators import validar_rut_chileno
from usuarios.base import SoftDeleteModel

class Paciente(SoftDeleteModel):
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]

    rut = models.CharField(
        max_length=12,
        unique=True,
        validators=[validar_rut_chileno],
        verbose_name="RUT Chileno"
    )
    nombres = models.CharField(max_length=100, verbose_name="Nombres")
    apellidos = models.CharField(max_length=100, verbose_name="Apellidos")
    fecha_nacimiento = models.DateField(verbose_name="Fecha de Nacimiento")
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, verbose_name="Sexo")
    telefono = models.CharField(max_length=15, verbose_name="Teléfono de Contacto")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")
    direccion = models.CharField(max_length=200, blank=True, null=True, verbose_name="Dirección de Domicilio")

    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.rut})"


class AntecedenteMedico(SoftDeleteModel):
    """
    Anamnesis del paciente: Registro de condiciones médicas relevantes
    antes o durante la atención odontológica.
    """
    paciente = models.OneToOneField(
        Paciente,
        on_delete=models.CASCADE,
        related_name='antecedentes_medicos',
        verbose_name="Paciente"
    )
    alergias = models.TextField(blank=True, null=True, verbose_name="Alergias Conocidas (Fármacos/Latex)")
    enfermedades_cronicas = models.TextField(blank=True, null=True, verbose_name="Enfermedades Crónicas (Diabetes, Hipertensión, etc.)")
    medicamentos_actuales = models.TextField(blank=True, null=True, verbose_name="Medicamentos en Uso")
    fuma = models.BooleanField(default=False, verbose_name="¿Es Fumador?")
    embarazada = models.BooleanField(default=False, verbose_name="¿Está Embarazada?")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones Adicionales")

    class Meta:
        verbose_name = "Antecedente Médico"
        verbose_name_plural = "Antecedentes Médicos"

    def __str__(self):
        return f"Anamnesis de {self.paciente.nombres} {self.paciente.apellidos}"


class FichaClinica(SoftDeleteModel):
    """
    Ficha Clínica Odontológica: Contenedor general del historial médico.
    Garantiza la trazabilidad exigida por la regulación de salud.
    """
    numero_ficha = models.CharField(max_length=20, unique=True, verbose_name="Número de Ficha")
    paciente = models.OneToOneField(
        Paciente,
        on_delete=models.PROTECT,
        related_name='ficha_clinica',
        verbose_name="Paciente"
    )
    fecha_apertura = models.DateField(auto_now_add=True, verbose_name="Fecha de Apertura")
    observaciones_generales = models.TextField(blank=True, null=True, verbose_name="Observaciones Generales")

    class Meta:
        verbose_name = "Ficha Clínica"
        verbose_name_plural = "Fichas Clínicas"

    def __str__(self):
        return f"Ficha N°{self.numero_ficha} - {self.paciente}"
