from django.db import models
from django.contrib.auth.models import AbstractUser
from .validators import validar_rut_chileno
from .base import SoftDeleteModel

class RolUsuario(SoftDeleteModel):
    ROLES = [
        ('ADMIN', 'Administrador'),
        ('RECEPCION', 'Recepcionista'),
        ('ODONTOLOGO', 'Odontólogo'),
        ('PACIENTE', 'Paciente'),
    ]
    nombre = models.CharField(max_length=20, choices=ROLES, unique=True)
    descripcion = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return self.get_nombre_display()

class Usuario(AbstractUser, SoftDeleteModel):
    rut = models.CharField(
        max_length=12,
        unique=True,
        validators=[validar_rut_chileno],
        verbose_name="RUT Chileno"
    )
    telefono = models.CharField(max_length=15, blank=True, null=True)
    rol = models.ForeignKey(
        RolUsuario,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='usuarios'
    )

    REQUIRED_FIELDS = ['email', 'rut']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.rut})"