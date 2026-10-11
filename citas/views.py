from datetime import date, datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from usuarios.models import Odontologo, Paciente, RolUsuario
from usuarios.permisos import rol_requerido

from .forms import CitaPacienteForm, CitaRecepcionForm
from .models import Cita

RELACIONES = ('paciente__usuario', 'odontologo__usuario', 'tipo_atencion')


def _url_lista(usuario):
    """Pantalla de citas a la que vuelve cada rol."""
    nombre = {
        RolUsuario.PACIENTE: 'mis_citas',
        RolUsuario.ODONTOLOGO: 'citas_odontologo',
        RolUsuario.RECEPCIONISTA: 'agenda_dia',
    }.get(usuario.rol, 'panel')
    return reverse(nombre)


def _inicio_del_dia(fecha):
    # Rango en vez de __date: en MariaDB __date falla con zonas horarias si
    # no se cargaron las tablas de zonas horarias del servidor.
    return timezone.make_aware(datetime.combine(fecha, time.min))


# --- Paciente ----------------------------------------------------------------
@rol_requerido(RolUsuario.PACIENTE)
def reservar_cita(request):
    paciente = get_object_or_404(Paciente, usuario=request.user)
    form = CitaPacienteForm(request.POST or None, instance=Cita(paciente=paciente))
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tu cita fue reservada.')
        return redirect('mis_citas')
    return render(request, 'formulario.html', {
        'titulo': 'Reservar cita',
        'form': form, 'texto_boton': 'Reservar cita',
        'url_cancelar': reverse('mis_citas'),
    })


@rol_requerido(RolUsuario.PACIENTE)
def mis_citas(request):
    paciente = get_object_or_404(Paciente, usuario=request.user)
    citas = Cita.objects.filter(paciente=paciente).select_related(*RELACIONES)
    return render(request, 'citas/lista_citas.html', {
        'titulo': 'Mis citas', 'citas': citas,
        'mostrar_paciente': False, 'mostrar_odontologo': True,
        'puede_cancelar': True, 'url_nueva': reverse('reservar_cita'),
    })


# --- Recepción ---------------------------------------------------------------
@rol_requerido(RolUsuario.RECEPCIONISTA)
def agendar_cita(request):
    form = CitaRecepcionForm(request.POST or None, instance=Cita())
    if request.method == 'POST' and form.is_valid():
        cita = form.save()
        messages.success(request, 'Cita agendada.')
        return redirect(f"{reverse('agenda_dia')}?fecha={cita.fecha_hora.date().isoformat()}")
    return render(request, 'formulario.html', {
        'titulo': 'Agendar cita presencial',
        'form': form, 'texto_boton': 'Agendar cita',
        'url_cancelar': reverse('agenda_dia'),
    })


@rol_requerido(RolUsuario.RECEPCIONISTA)
def agenda_dia(request):
    try:
        fecha = date.fromisoformat(request.GET.get('fecha', ''))
    except ValueError:
        fecha = timezone.localdate()
    inicio = _inicio_del_dia(fecha)
    citas = (Cita.objects
             .filter(fecha_hora__gte=inicio, fecha_hora__lt=inicio + timedelta(days=1))
             .select_related(*RELACIONES))
    return render(request, 'citas/lista_citas.html', {
        'titulo': f'Agenda del {fecha:%d/%m/%Y}', 'citas': citas,
        'mostrar_paciente': True, 'mostrar_odontologo': True,
        'puede_cancelar': True, 'url_nueva': reverse('agendar_cita'),
    })


# --- Odontólogo --------------------------------------------------------------
@rol_requerido(RolUsuario.ODONTOLOGO)
def citas_odontologo(request):
    odontologo = get_object_or_404(Odontologo, usuario=request.user)
    desde = _inicio_del_dia(timezone.localdate())
    citas = (Cita.objects
             .filter(odontologo=odontologo, fecha_hora__gte=desde)
             .exclude(estado='CANCELADA')
             .select_related(*RELACIONES))
    return render(request, 'citas/lista_citas.html', {
        'titulo': 'Mis citas', 'citas': citas,
        'mostrar_paciente': True, 'mostrar_odontologo': False,
        'puede_cancelar': False,
    })


# --- Comunes -----------------------------------------------------------------
@login_required
def detalle_cita(request, pk):
    cita = get_object_or_404(Cita.objects.select_related(*RELACIONES), pk=pk)
    u = request.user
    propia = (
        (u.rol == RolUsuario.PACIENTE and cita.paciente.usuario_id == u.id)
        or (u.rol == RolUsuario.ODONTOLOGO and cita.odontologo.usuario_id == u.id)
    )
    if not (propia or u.rol in (RolUsuario.RECEPCIONISTA, RolUsuario.ADMINISTRADOR)):
        raise PermissionDenied
    return render(request, 'citas/detalle_cita.html', {
        'cita': cita, 'url_volver': _url_lista(u),
    })


@login_required
@require_POST
def cancelar_cita(request, pk):
    cita = get_object_or_404(Cita.objects.select_related('paciente'), pk=pk)
    u = request.user
    puede = (
        u.rol in (RolUsuario.RECEPCIONISTA, RolUsuario.ADMINISTRADOR)
        or (u.rol == RolUsuario.PACIENTE and cita.paciente.usuario_id == u.id)
    )
    if not puede:
        raise PermissionDenied
    try:
        cita.cancelar()
        messages.success(request, 'La cita fue cancelada.')
    except ValidationError as e:
        messages.error(request, ' '.join(e.messages))
    return redirect(_url_lista(u))