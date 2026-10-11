from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from citas.models import Cita, EstadoCita, TipoAtencion
from usuarios.models import RolUsuario
from usuarios.permisos import rol_requerido

from .forms import AntecedentesForm, AtencionForm, InsumoFormSet, TratamientoFormSet
from .models import Atencion, FichaClinica, Presupuesto, Tratamiento

ESTADOS_ATENDIBLES = (EstadoCita.RESERVADA, EstadoCita.CONFIRMADA, EstadoCita.EN_ATENCION)


@rol_requerido(RolUsuario.ODONTOLOGO)
def fichas(request):
    q = request.GET.get('q', '').strip()
    qs = (FichaClinica.objects.select_related('paciente__usuario')
          .order_by('paciente__usuario__last_name', 'paciente__usuario__first_name'))
    if q:
        qs = qs.filter(
            Q(paciente__rut__icontains=q.replace('.', ''))
            | Q(paciente__usuario__first_name__icontains=q)
            | Q(paciente__usuario__last_name__icontains=q))
    return render(request, 'clinica/fichas.html', {'fichas': qs[:50], 'q': q})


@rol_requerido(RolUsuario.ODONTOLOGO)
def ficha_detalle(request, pk):
    ficha = get_object_or_404(FichaClinica.objects.select_related('paciente__usuario'), pk=pk)
    form = AntecedentesForm(request.POST or None, instance=ficha)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Antecedentes actualizados.')
        return redirect('ficha_detalle', pk=pk)

    atenciones = ficha.atenciones.select_related('cita').prefetch_related('tratamientos')
    # Solo las citas propias del odontólogo con este paciente que aún no se atendieron.
    citas_pendientes = (Cita.objects
                        .filter(paciente=ficha.paciente, odontologo__usuario=request.user,
                                estado__in=ESTADOS_ATENDIBLES, atencion__isnull=True)
                        .select_related('tipo_atencion'))
    return render(request, 'clinica/ficha_detalle.html', {
        'ficha': ficha, 'form_antecedentes': form,
        'atenciones': atenciones, 'citas_pendientes': citas_pendientes,
    })


@rol_requerido(RolUsuario.ODONTOLOGO)
def registrar_atencion(request, cita_id):
    cita = get_object_or_404(
        Cita.objects.select_related('paciente__usuario', 'odontologo__usuario', 'tipo_atencion'),
        pk=cita_id)
    if cita.odontologo.usuario_id != request.user.id:
        raise PermissionDenied
    if cita.estado not in ESTADOS_ATENDIBLES or Atencion.objects.filter(cita=cita).exists():
        messages.error(request, 'Esta cita ya no se puede atender.')
        return redirect('citas_odontologo')

    form = AtencionForm(request.POST or None)
    fs_tratamientos = TratamientoFormSet(request.POST or None, prefix='tratamientos')
    fs_insumos = InsumoFormSet(request.POST or None, prefix='insumos')

    if request.method == 'POST':
        validos = [form.is_valid(), fs_tratamientos.is_valid(), fs_insumos.is_valid()]
        if all(validos):
            tipos = [f.cleaned_data['tipo_atencion'] for f in fs_tratamientos.forms if f.cleaned_data]
            insumos = [(f.cleaned_data['insumo'], f.cleaned_data['cantidad'])
                       for f in fs_insumos.forms if f.cleaned_data]
            sin_insumos = form.cleaned_data['sin_insumos']

            if sin_insumos and insumos:
                form.add_error(None, 'Marcaste que no se usaron insumos, pero agregaste filas de insumos.')
            elif not sin_insumos and not insumos:
                form.add_error(None, 'Agrega los insumos utilizados o marca que no se utilizaron.')
            else:
                try:
                    with transaction.atomic():  # si algo falla, no se guarda nada
                        ficha, _ = FichaClinica.objects.get_or_create(paciente=cita.paciente)
                        atencion = Atencion.objects.create(
                            ficha=ficha, cita=cita, fecha_hora=timezone.now(),
                            diagnostico=form.cleaned_data['diagnostico'])
                        for tipo in tipos:
                            Tratamiento.objects.create(atencion=atencion, tipo_atencion=tipo)
                        Presupuesto.objects.create(atencion=atencion).calcular_total()
                        for insumo, cantidad in insumos:
                            atencion.registrar_insumo(insumo, cantidad)  # falla si no hay stock
                        cita.estado = EstadoCita.COMPLETADA
                        cita.save(update_fields=['estado'])
                except ValidationError as e:
                    for mensaje in e.messages:
                        form.add_error(None, mensaje)
                else:
                    messages.success(request, 'Atención registrada.')
                    return redirect('ficha_detalle', pk=ficha.pk)

    precios = {str(t.pk): str(t.costo) for t in TipoAtencion.objects.filter(activo=True)}
    return render(request, 'clinica/registrar_atencion.html', {
        'cita': cita, 'form': form,
        'formset_tratamientos': fs_tratamientos, 'formset_insumos': fs_insumos,
        'precios': precios,
    })