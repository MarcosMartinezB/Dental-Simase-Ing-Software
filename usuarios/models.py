from django.contrib.auth import logout
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .base import SoftDeleteModel, SoftDeleteQuerySet
from .validators import normalizar_rut, validar_rut_chileno


class RolUsuario(models.TextChoices):
    PACIENTE = 'PACIENTE', 'Paciente'
    RECEPCIONISTA = 'RECEPCIONISTA', 'Recepcionista / Cajero'
    ODONTOLOGO = 'ODONTOLOGO', 'Odontólogo'
    INVENTARIO = 'INVENTARIO', 'Encargado de Inventario'
    ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'


class UsuarioQuerySet(SoftDeleteQuerySet):
    def delete(self):
        return self.update(activo=False, is_active=False,
                           modificado_en=timezone.now())


class UsuarioManager(UserManager.from_queryset(UsuarioQuerySet)):
    def get_queryset(self):
        return super().get_queryset().filter(activo=True)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('rol', RolUsuario.ADMINISTRADOR)
        return super().create_superuser(username, email, password, **extra_fields)


class UsuarioTodosManager(UserManager.from_queryset(UsuarioQuerySet)):
    pass


class Usuario(AbstractUser, SoftDeleteModel):
    # El hash de la contraseña lo guarda el campo `password` de AbstractUser.
    rol = models.CharField(
        max_length=15, choices=RolUsuario.choices, default=RolUsuario.PACIENTE
    )

    REQUIRED_FIELDS = ['email']

    objects = UsuarioManager()
    all_objects = UsuarioTodosManager()

    @property
    def nombre_completo(self):
        return self.get_full_name()

    def save(self, *args, **kwargs):
        self.is_active = self.activo  # una sola fuente de verdad
        super().save(*args, **kwargs)

    def autenticar(self, password):
        return self.is_active and self.check_password(password)

    def cambiar_password(self, clave_actual, nueva_clave):
        if not self.check_password(clave_actual):
            raise ValidationError('La contraseña actual no es correcta.')
        validate_password(nueva_clave, self)
        self.set_password(nueva_clave)
        self.save(update_fields=['password'])

    def cerrar_sesion(self, request):
        logout(request)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"


class Paciente(models.Model):
    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE, related_name='perfil_paciente'
    )
    rut = models.CharField(
        max_length=12, unique=True, validators=[validar_rut_chileno],
        verbose_name="RUT"
    )
    telefono = models.CharField(max_length=15, blank=True)
    fecha_nacimiento = models.DateField()

    def clean(self):
        if self.rut:
            self.rut = normalizar_rut(self.rut)

    def save(self, *args, **kwargs):
        if self.rut:
            self.rut = normalizar_rut(self.rut)
        super().save(*args, **kwargs)

    def reservar_cita(self, fecha_hora, odontologo):
        from citas.models import Cita
        cita = Cita(paciente=self, odontologo=odontologo, fecha_hora=fecha_hora)
        cita.full_clean()
        cita.save()
        return cita

    def consultar_mis_citas(self):
        return self.citas.all()

    def __str__(self):
        return f"{self.usuario.get_full_name()} ({self.rut})"


class Odontologo(models.Model):
    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE, related_name='perfil_odontologo'
    )
    especialidad = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Odontólogo"
        verbose_name_plural = "Odontólogos"

    def consultar_ficha(self, paciente):
        return paciente.ficha_clinica

    def registrar_atencion(self, cita):
        from fichas.models import Atencion, FichaClinica
        if cita.odontologo_id != self.pk:
            raise ValidationError('Esta cita no corresponde a este odontólogo.')
        ficha, _ = FichaClinica.objects.get_or_create(paciente=cita.paciente)
        return Atencion.objects.create(
            ficha=ficha, cita=cita, fecha_hora=timezone.now()
        )

    def __str__(self):
        return f"Dr(a). {self.usuario.get_full_name()} - {self.especialidad}"