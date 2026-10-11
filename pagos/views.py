from django.contrib import messages
from django.contrib.admin.models import CHANGE
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from citas.models import Cita, EstadoCita
from usuarios import auditoria
from usuarios.models import RolUsuario
from usuarios.permisos import rol_requerido

from . import servicios
from .estrategias import PagoEfectivo, PagoTarjetaPresencial
from .forms import DevolucionForm, PagoForm
from .models import EstadoPago, MedioPago, Pago

RELACIONES = ('paciente__usuario', 'odontologo__usuario', 'tipo_atencion', 'atencion', 'pago')


@rol_requerido(RolUsuario.RECEPCIONISTA)
def cobros(request):
    """Citas con pago pendiente: desde aquí recepción elige cuál cobrar."""
    q = request.GET.get('q', '').strip()
    citas = (Cita.objects.exclude(estado=EstadoCita.CANCELADA)
             .exclude(pago__estado=EstadoPago.APROBADO)
             .select_related(*RELACIONES).order_by('-fecha_hora'))
    if q:
        citas = citas.filter(
            Q(paciente__rut__icontains=q.replace('.', ''))
            | Q(paciente__usuario__first_name__icontains=q)
            | Q(paciente__usuario__last_name__icontains=q))
    filas = [(c, servicios.monto_pendiente(c)) for c in citas[:50]]
    return render(request, 'recepcion/cobros.html', {'filas': filas, 'q': q})


@rol_requerido(RolUsuario.RECEPCIONISTA)
def registrar_pago(request, cita_id):
    cita = get_object_or_404(Cita.objects.select_related(*RELACIONES), pk=cita_id)
    if cita.estado == EstadoCita.CANCELADA:
        messages.error(request, 'No se puede cobrar una cita cancelada.')
        return redirect('cobros')
    existente = Pago.objects.filter(cita=cita).first()
    if existente and existente.estado == EstadoPago.APROBADO:
        messages.info(request, 'Esta cita ya tiene un pago aprobado.')
        return redirect('comprobante', pk=existente.pk)

    monto = servicios.monto_pendiente(cita)
    form = PagoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        if d['medio'] == MedioPago.EFECTIVO:
            estrategia = PagoEfectivo(d['monto_recibido'])
        else:
            estrategia = PagoTarjetaPresencial(d['referencia_pos'], d['resultado_pos'])
        try:
            pago = servicios.registrar_pago(cita, estrategia, monto)
        except ValidationError as e:
            for mensaje in e.messages:
                form.add_error(None, mensaje)
        else:
            if pago.estado == EstadoPago.APROBADO:
                messages.success(request, 'Pago aprobado.')
                return redirect('comprobante', pk=pago.pk)
            # Rechazado: se informa el motivo y no se genera comprobante.
            messages.error(request, f'Pago rechazado. {pago.motivo_rechazo}')
            return redirect('registrar_pago', cita_id=cita.pk)

    return render(request, 'recepcion/registrar_pago.html', {
        'cita': cita, 'monto': monto, 'form': form,
    })


@rol_requerido(RolUsuario.RECEPCIONISTA, RolUsuario.ADMINISTRADOR)
def comprobante(request, pk):
    pago = get_object_or_404(
        Pago.objects.select_related('cita__paciente__usuario', 'cita__odontologo__usuario',
                                    'cita__tipo_atencion', 'comprobante'), pk=pk)
    emitido = getattr(pago, 'comprobante', None)
    if emitido is None:  # solo los pagos aprobados tienen comprobante
        raise Http404
    vuelto = None
    if pago.medio == MedioPago.EFECTIVO:
        vuelto = pago.estrategia.calcular_vuelto(pago.monto)
    return render(request, 'recepcion/comprobante.html', {
        'pago': pago, 'comprobante': emitido, 'cita': pago.cita, 'vuelto': vuelto,
    })


# --- Devoluciones: citas canceladas que ya estaban pagadas ----------------------
@rol_requerido(RolUsuario.RECEPCIONISTA)
def devoluciones(request):
    pagos = (Pago.objects
             .filter(estado=EstadoPago.APROBADO, cita__estado=EstadoCita.CANCELADA)
             .select_related('cita__paciente__usuario', 'cita__tipo_atencion')
             .order_by('cita__fecha_hora'))
    return render(request, 'recepcion/devoluciones.html', {'pagos': pagos})


@rol_requerido(RolUsuario.RECEPCIONISTA)
def registrar_devolucion(request, pago_id):
    pago = get_object_or_404(
        Pago.objects.select_related('cita__paciente__usuario'), pk=pago_id)
    if pago.estado != EstadoPago.APROBADO or pago.cita.estado != EstadoCita.CANCELADA:
        messages.error(request, 'Este pago no tiene una devolución pendiente.')
        return redirect('devoluciones')

    form = DevolucionForm(request.POST or None, medio=pago.medio)
    if request.method == 'POST' and form.is_valid():
        try:
            pago.reembolsar(form.cleaned_data.get('referencia_reembolso', ''))
        except ValidationError as e:
            for mensaje in e.messages:
                form.add_error(None, mensaje)
        else:
            auditoria.registrar(request.user, pago, CHANGE,
                                f'Devolución registrada por ${pago.monto:,.0f}.'.replace(',', '.'))
            messages.success(request, 'Devolución registrada.')
            return redirect('devoluciones')

    como = ('en efectivo' if pago.medio == MedioPago.EFECTIVO
            else 'con la reversa de la operación en el POS')
    monto = f'${pago.monto:,.0f}'.replace(',', '.')
    return render(request, 'formulario.html', {
        'titulo': 'Registrar devolución',
        'subtitulo': f'Devolver {monto} a {pago.cita.paciente} {como}. '
                     'Confirma aquí cuando ya se haya devuelto el dinero.',
        'form': form, 'texto_boton': 'Confirmar devolución',
        'url_cancelar': reverse('devoluciones'),
    })
