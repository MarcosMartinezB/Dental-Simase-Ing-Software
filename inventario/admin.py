import csv

from django.contrib import admin
from django.db.models import F
from django.http import HttpResponse

from .models import Insumo, MovimientoInventario


class StockBajoFilter(admin.SimpleListFilter):
    title = 'alerta de reabastecimiento'
    parameter_name = 'stock'

    def lookups(self, request, model_admin):
        return [('bajo', 'Bajo el mínimo'), ('ok', 'Stock suficiente')]

    def queryset(self, request, queryset):
        if self.value() == 'bajo':
            return queryset.filter(stock_actual__lt=F('stock_minimo'))
        if self.value() == 'ok':
            return queryset.filter(stock_actual__gte=F('stock_minimo'))
        return queryset


@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'stock_actual', 'stock_minimo', 'stock_suficiente')
    list_filter = (StockBajoFilter,)
    search_fields = ('codigo', 'nombre')
    actions = ['exportar_stock_csv']

    @admin.display(boolean=True, description='Stock suficiente')
    def stock_suficiente(self, obj):
        return obj.verificar_stock_minimo()

    def get_readonly_fields(self, request, obj=None):
        # El stock solo cambia mediante movimientos, nunca a mano.
        return ('stock_actual',) if obj else ()

    @admin.action(description='Exportar stock seleccionado a CSV')
    def exportar_stock_csv(self, request, queryset):
        resp = HttpResponse(content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = 'attachment; filename="stock_insumos.csv"'
        w = csv.writer(resp)
        w.writerow(['Código', 'Nombre', 'Stock actual', 'Stock mínimo', 'Estado'])
        for i in queryset:
            w.writerow([i.codigo, i.nombre, i.stock_actual, i.stock_minimo,
                        'OK' if i.verificar_stock_minimo() else 'REABASTECER'])
        return resp


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora', 'tipo', 'insumo', 'cantidad', 'usuario', 'atencion')
    list_filter = ('tipo', 'fecha_hora')
    search_fields = ('insumo__codigo', 'insumo__nombre', 'usuario__username')
    autocomplete_fields = ('insumo',)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # un movimiento ya registrado no se edita
            return ('insumo', 'usuario', 'atencion', 'fecha_hora', 'tipo', 'cantidad')
        return ('usuario',)  # al crear, el usuario es quien está logueado

    def save_model(self, request, obj, form, change):
        obj.usuario = request.user
        obj.save()  # pasa por registrar() y actualiza el stock

    def has_delete_permission(self, request, obj=None):
        return False  # los movimientos no se borran: se corrigen con otro movimiento