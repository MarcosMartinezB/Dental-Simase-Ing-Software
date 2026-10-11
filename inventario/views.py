import csv

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from usuarios.models import RolUsuario
from usuarios.permisos import rol_requerido

from .forms import InsumoForm, MovimientoForm
from .models import Insumo, MovimientoInventario, TipoMovimiento


@rol_requerido(RolUsuario.INVENTARIO)
def stock(request):
    bajo = Insumo.objects.filter(stock_actual__lt=F('stock_minimo'))
    solo_bajo = request.GET.get('estado') == 'bajo'
    return render(request, 'inventario/stock.html', {
        'insumos': bajo if solo_bajo else Insumo.objects.all(),
        'cantidad_bajo': bajo.count(),
        'solo_bajo': solo_bajo,
    })


@rol_requerido(RolUsuario.INVENTARIO)
def crear_insumo(request):
    form = InsumoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                insumo = form.save()
                inicial = form.cleaned_data['stock_inicial']
                if inicial:
                    MovimientoInventario(
                        insumo=insumo, usuario=request.user,
                        tipo=TipoMovimiento.ENTRADA, cantidad=inicial).registrar()
        except ValidationError as e:
            for mensaje in e.messages:
                form.add_error(None, mensaje)
        else:
            messages.success(request, f'Insumo {insumo.nombre} creado.')
            return redirect('stock')
    return render(request, 'formulario.html', {
        'titulo': 'Nuevo insumo', 'form': form, 'texto_boton': 'Crear insumo',
        'url_cancelar': reverse('stock'),
    })


@rol_requerido(RolUsuario.INVENTARIO)
def registrar_movimiento(request):
    form = MovimientoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        movimiento = form.save(commit=False)
        movimiento.usuario = request.user
        try:
            movimiento.registrar()  # actualiza el stock; falla si quedaría negativo
        except ValidationError as e:
            for mensaje in e.messages:
                form.add_error(None, mensaje)
        else:
            messages.success(request, f'Movimiento registrado: {movimiento}.')
            return redirect('stock')
    return render(request, 'formulario.html', {
        'titulo': 'Registrar movimiento',
        'subtitulo': 'Entrada por compra o salida a box clínico. El stock se actualiza solo.',
        'form': form, 'texto_boton': 'Registrar',
        'url_cancelar': reverse('stock'),
    })


@rol_requerido(RolUsuario.INVENTARIO)
def exportar_stock(request):
    respuesta = HttpResponse(content_type='text/csv; charset=utf-8')
    respuesta['Content-Disposition'] = 'attachment; filename="stock_insumos.csv"'
    respuesta.write('\ufeff')  # para que Excel respete tildes y ñ
    escritor = csv.writer(respuesta, delimiter=';')
    escritor.writerow(['Código', 'Nombre', 'Stock actual', 'Stock mínimo', 'Estado'])
    for i in Insumo.objects.all():
        escritor.writerow([i.codigo, i.nombre, i.stock_actual, i.stock_minimo,
                           'OK' if i.verificar_stock_minimo() else 'REABASTECER'])
    return respuesta
