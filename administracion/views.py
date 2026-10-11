from smtplib import SMTPException
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from citas.models import TipoAtencion
from usuarios import auditoria
from usuarios.models import RolUsuario
from usuarios.permisos import rol_requerido

from . import reportes
from .forms import TipoAtencionForm
from .pdf import generar_pdf

ADMIN = RolUsuario.ADMINISTRADOR


# --- Configurar aranceles de servicios --------------------------------------
@rol_requerido(ADMIN)
def aranceles(request):
    return render(request, 'administracion/aranceles.html', {'tipos': TipoAtencion.objects.all()})


@rol_requerido(ADMIN)
def crear_arancel(request):
    form = TipoAtencionForm(request.POST or None, initial={'activo': True})
    if request.method == 'POST' and form.is_valid():
        tipo = form.save()
        auditoria.registrar(request.user, tipo, ADDITION, 'Arancel creado.')
        messages.success(request, f'Atención «{tipo.nombre}» creada.')
        return redirect('aranceles')
    return render(request, 'formulario.html', {
        'titulo': 'Nueva atención', 'form': form, 'texto_boton': 'Crear atención',
        'url_cancelar': reverse('aranceles'),
    })


@rol_requerido(ADMIN)
def editar_arancel(request, pk):
    tipo = get_object_or_404(TipoAtencion, pk=pk)
    form = TipoAtencionForm(request.POST or None, instance=tipo)
    if request.method == 'POST' and form.is_valid():
        tipo = form.save()
        if form.changed_data:
            auditoria.registrar(request.user, tipo, CHANGE,
                                'Arancel modificado: ' + ', '.join(form.changed_data) + '.')
        messages.success(request, f'Atención «{tipo.nombre}» actualizada.')
        return redirect('aranceles')
    return render(request, 'formulario.html', {
        'titulo': f'Editar atención: {tipo.nombre}', 'form': form,
        'texto_boton': 'Guardar cambios', 'url_cancelar': reverse('aranceles'),
    })


# --- Generar reporte de gestión ----------------------------------------------
@rol_requerido(ADMIN)
def reportes_gestion(request):
    desde, hasta = reportes.leer_rango(request.GET)
    return render(request, 'administracion/reportes.html', {
        'desde': desde.isoformat(), 'hasta': hasta.isoformat(),
        'resumen': reportes.construir_resumen(desde, hasta),
    })


@rol_requerido(ADMIN)
def reporte_pdf(request):
    desde, hasta = reportes.leer_rango(request.GET)
    pdf = generar_pdf(desde, hasta, reportes.construir_resumen(desde, hasta),
                      generado_por=request.user.get_full_name() or request.user.username)
    respuesta = HttpResponse(pdf, content_type='application/pdf')
    respuesta['Content-Disposition'] = f'attachment; filename="reporte_{desde}_{hasta}.pdf"'
    return respuesta


@rol_requerido(ADMIN)
@require_POST
def reporte_correo(request):
    desde, hasta = reportes.leer_rango(request.POST)
    volver = f"{reverse('reportes')}?{urlencode({'desde': desde, 'hasta': hasta})}"
    if not request.user.email:
        messages.error(request, 'Tu usuario no tiene un correo registrado para recibir el reporte.')
        return redirect(volver)

    resumen = reportes.construir_resumen(desde, hasta)
    cuerpo = (f'Reporte de gestión de Dental Simase\n'
              f'Período: {desde:%d/%m/%Y} al {hasta:%d/%m/%Y}\n\n'
              + '\n'.join(f'{etiqueta}: {valor}' for etiqueta, valor in resumen))
    correo = EmailMessage(
        subject=f'Reporte de gestión Dental Simase ({desde:%d/%m/%Y} - {hasta:%d/%m/%Y})',
        body=cuerpo, to=[request.user.email])
    correo.attach(f'reporte_{desde}_{hasta}.pdf',
                  generar_pdf(desde, hasta, resumen,
                              generado_por=request.user.get_full_name() or request.user.username),
                  'application/pdf')
    try:
        correo.send()
        messages.success(request, f'Reporte enviado a {request.user.email}.')
    except (SMTPException, OSError):
        messages.error(request, 'No se pudo enviar el correo. Revisa la configuración de correo.')
    return redirect(volver)
