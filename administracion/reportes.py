from datetime import date, datetime, time, timedelta

from django.db.models import Count, F, Sum
from django.utils import timezone

from citas.models import Cita, EstadoCita
from fichas.models import Atencion, Tratamiento
from inventario.models import Insumo, MovimientoInventario, TipoMovimiento
from pagos.models import EstadoPago, MedioPago, Pago


def clp(valor):
    return '$' + f'{valor or 0:,.0f}'.replace(',', '.')


def leer_rango(params):
    """Lee ?desde= y ?hasta= (YYYY-MM-DD). Por defecto, los últimos 30 días."""
    hoy = timezone.localdate()
    try:
        desde = date.fromisoformat(params.get('desde', ''))
    except ValueError:
        desde = hoy - timedelta(days=30)
    try:
        hasta = date.fromisoformat(params.get('hasta', ''))
    except ValueError:
        hasta = hoy
    if desde > hasta:
        desde, hasta = hasta, desde
    return desde, hasta


def construir_resumen(desde, hasta):
    """Lista de (indicador, valor) para el rango de fechas, ambos extremos incluidos."""
    inicio = timezone.make_aware(datetime.combine(desde, time.min))
    fin = timezone.make_aware(datetime.combine(hasta, time.min)) + timedelta(days=1)

    citas = Cita.objects.filter(fecha_hora__gte=inicio, fecha_hora__lt=fin)
    por_estado = dict(citas.values_list('estado').annotate(n=Count('id')))
    filas = [('Citas en el período', citas.count())]
    filas += [(f'   - {etiqueta}', por_estado.get(valor, 0)) for valor, etiqueta in EstadoCita.choices]

    filas.append(('Atenciones realizadas',
                  Atencion.objects.filter(fecha_hora__gte=inicio, fecha_hora__lt=fin).count()))
    frecuente = (Tratamiento.objects
                 .filter(atencion__fecha_hora__gte=inicio, atencion__fecha_hora__lt=fin)
                 .values('nombre').annotate(n=Count('id')).order_by('-n', 'nombre').first())
    filas.append(('Atención más frecuente',
                  f"{frecuente['nombre']} ({frecuente['n']})" if frecuente else '-'))

    pagos = Pago.objects.filter(fecha_pago__gte=inicio, fecha_pago__lt=fin)
    aprobados = pagos.filter(estado=EstadoPago.APROBADO)
    por_medio = dict(aprobados.values_list('medio').annotate(t=Sum('monto')))
    filas += [
        ('Pagos aprobados', aprobados.count()),
        ('Total recaudado', clp(aprobados.aggregate(t=Sum('monto'))['t'])),
        ('   - En efectivo', clp(por_medio.get(MedioPago.EFECTIVO))),
        ('   - Con tarjeta presencial', clp(por_medio.get(MedioPago.TARJETA_PRESENCIAL))),
        ('Pagos rechazados', pagos.filter(estado=EstadoPago.RECHAZADO).count()),
    ]

    movimientos = MovimientoInventario.objects.filter(fecha_hora__gte=inicio, fecha_hora__lt=fin)
    por_tipo = dict(movimientos.values_list('tipo').annotate(t=Sum('cantidad')))
    filas += [
        ('Insumos ingresados (unidades)', por_tipo.get(TipoMovimiento.ENTRADA, 0)),
        ('Insumos utilizados (unidades)', por_tipo.get(TipoMovimiento.SALIDA, 0)),
        ('Insumos bajo el mínimo (hoy)',
         Insumo.objects.filter(stock_actual__lt=F('stock_minimo')).count()),
    ]
    return filas
