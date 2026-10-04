import secrets
import string

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .models import Odontologo, Paciente, RolUsuario, Usuario
from .validators import normalizar_rut

ROLES_QUE_PUEDE_CREAR = {
    RolUsuario.ADMINISTRADOR: {
        RolUsuario.ODONTOLOGO, RolUsuario.RECEPCIONISTA, RolUsuario.INVENTARIO,
    },
    RolUsuario.RECEPCIONISTA: {RolUsuario.PACIENTE},
}


def roles_creables(creador):
    if creador.is_superuser:
        return {RolUsuario.ADMINISTRADOR}
    return ROLES_QUE_PUEDE_CREAR.get(creador.rol, set())


def verificar_permiso(creador, rol):
    if rol not in roles_creables(creador):
        raise PermissionDenied('No tiene permiso para crear usuarios con ese rol.')


def generar_password(largo=12):
    alfabeto = string.ascii_letters + string.digits + '!@#$%&*'
    while True:
        clave = ''.join(secrets.choice(alfabeto) for _ in range(largo))
        if (any(c.islower() for c in clave) and any(c.isupper() for c in clave)
                and any(c.isdigit() for c in clave)
                and any(c in '!@#$%&*' for c in clave)):
            return clave


@transaction.atomic
def crear_usuario_interno(creador, rol, *, username, email, first_name,
                          last_name, especialidad=''):
    """Administrador/superusuario crea personal. Devuelve (usuario, clave_temporal)."""
    verificar_permiso(creador, rol)
    clave = generar_password()
    usuario = Usuario(username=username, email=email, first_name=first_name,
                      last_name=last_name, rol=rol)
    usuario.set_password(clave)
    usuario.full_clean()
    usuario.save()
    if rol == RolUsuario.ODONTOLOGO:
        Odontologo.objects.create(usuario=usuario, especialidad=especialidad)
    return usuario, clave


@transaction.atomic
def registrar_paciente(creador, *, rut, email, first_name, last_name,
                       fecha_nacimiento, telefono=''):
    """Recepcionista registra un paciente. Devuelve (paciente, clave_temporal)."""
    verificar_permiso(creador, RolUsuario.PACIENTE)
    rut = normalizar_rut(rut)
    clave = generar_password()
    usuario = Usuario(username=rut, email=email, first_name=first_name,
                      last_name=last_name, rol=RolUsuario.PACIENTE)
    usuario.set_password(clave)
    usuario.full_clean()
    usuario.save()
    paciente = Paciente(usuario=usuario, rut=rut, telefono=telefono,
                        fecha_nacimiento=fecha_nacimiento)
    paciente.full_clean()
    paciente.save()
    return paciente, clave