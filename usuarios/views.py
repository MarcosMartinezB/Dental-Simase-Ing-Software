from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST

from . import auditoria, servicios
from .forms import PacienteRegistroForm, UsuarioInternoForm
from .models import RolUsuario, Usuario
from .permisos import rol_requerido


@login_required
def panel(request):
    return render(request, 'panel.html')


# --- Recepción ---------------------------------------------------------------
@rol_requerido(RolUsuario.RECEPCIONISTA)
def registrar_paciente(request):
    form = PacienteRegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        try:
            paciente, clave = servicios.registrar_paciente(
                request.user, rut=d['rut'], email=d['email'],
                first_name=d['first_name'], last_name=d['last_name'],
                fecha_nacimiento=d['fecha_nacimiento'], telefono=d['telefono'])
        except ValidationError as e:
            for mensaje in e.messages:
                form.add_error(None, mensaje)
        else:
            auditoria.registrar(request.user, paciente.usuario, ADDITION,
                                'Paciente registrado en recepción.')
            # Se renderiza directo (sin redirect) para que la clave no viaje en la URL.
            return render(request, 'credenciales.html', {
                'titulo': 'Paciente registrado',
                'usuario': paciente.usuario.username,
                'clave': clave,
                'url_volver': reverse('registrar_paciente'),
            })
    return render(request, 'formulario.html', {
        'titulo': 'Registrar paciente',
        'subtitulo': 'Se crea su usuario con una contraseña segura que podrás entregarle.',
        'form': form, 'texto_boton': 'Registrar paciente',
        'url_cancelar': reverse('panel'),
    })


# --- Cuenta propia -----------------------------------------------------------
class CambiarPasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'formulario.html'
    success_url = reverse_lazy('panel')
    success_message = 'Tu contraseña fue actualizada.'
    extra_context = {
        'titulo': 'Cambiar contraseña',
        'texto_boton': 'Actualizar contraseña',
        'url_cancelar': reverse_lazy('panel'),
    }


# --- Administración de usuarios ---------------------------------------------
@rol_requerido(RolUsuario.ADMINISTRADOR)
def gestionar_usuarios(request):
    creables = servicios.roles_creables(request.user)
    return render(request, 'administracion/usuarios.html', {
        'usuarios': Usuario.all_objects.order_by('username'),  # incluye inactivos
        'roles_creables': [(r.value, r.label) for r in RolUsuario if r in creables],
    })


@rol_requerido(RolUsuario.ADMINISTRADOR)
def crear_usuario(request, rol):
    if rol not in RolUsuario.values:
        raise Http404
    servicios.verificar_permiso(request.user, rol)  # 403 si el rol no corresponde

    form = UsuarioInternoForm(request.POST or None, rol=rol)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        try:
            usuario, clave = servicios.crear_usuario_interno(
                request.user, rol, username=d['username'], email=d['email'],
                first_name=d['first_name'], last_name=d['last_name'],
                especialidad=d.get('especialidad', ''))
        except ValidationError as e:
            for mensaje in e.messages:
                form.add_error(None, mensaje)
        else:
            auditoria.registrar(request.user, usuario, ADDITION,
                                f'Usuario creado con el rol {RolUsuario(rol).label}.')
            return render(request, 'credenciales.html', {
                'titulo': f'{RolUsuario(rol).label} creado',
                'usuario': usuario.username,
                'clave': clave,
                'url_volver': reverse('gestionar_usuarios'),
            })
    return render(request, 'formulario.html', {
        'titulo': f'Nuevo usuario: {RolUsuario(rol).label}',
        'form': form, 'texto_boton': 'Crear usuario',
        'url_cancelar': reverse('gestionar_usuarios'),
    })


@rol_requerido(RolUsuario.ADMINISTRADOR)
@require_POST
def cambiar_estado_usuario(request, pk):
    usuario = get_object_or_404(Usuario.all_objects, pk=pk)
    if usuario.pk == request.user.pk:
        messages.error(request, 'No puedes desactivar tu propia cuenta.')
    elif usuario.is_superuser and not request.user.is_superuser:
        raise PermissionDenied
    else:
        usuario.activo = not usuario.activo
        usuario.save()
        accion = 'reactivado' if usuario.activo else 'desactivado'
        auditoria.registrar(request.user, usuario, CHANGE, f'Usuario {accion}.')
        messages.success(request, f'Usuario {usuario.username} {accion}.')
    return redirect('gestionar_usuarios')
