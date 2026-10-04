from django.contrib import admin

from .models import ComprobantePago, Pago


class ComprobanteInline(admin.StackedInline):
    model = ComprobantePago
    can_delete = False
    extra = 0
    max_num = 0
    readonly_fields = ('numero', 'fecha_emision', 'monto_total')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cita', 'monto', 'medio', 'estado', 'fecha_pago')
    list_filter = ('estado', 'medio', 'fecha_pago')
    search_fields = ('cita__paciente__rut', 'cita__paciente__usuario__last_name',
                     'referencia_pos')
    inlines = [ComprobanteInline]

    def get_readonly_fields(self, request, obj=None):
        if obj:  # un pago registrado no se edita
            return ('cita', 'monto', 'medio', 'monto_recibido', 'referencia_pos',
                    'resultado_pos', 'estado', 'fecha_pago')
        return ('estado', 'fecha_pago')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.procesar()  # aplica la estrategia y genera el comprobante si se aprueba

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ComprobantePago)
class ComprobantePagoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'pago', 'fecha_emision', 'monto_total')
    search_fields = ('numero',)

    def has_add_permission(self, request):
        return False  # se generan automáticamente al aprobar un pago

    def has_delete_permission(self, request, obj=None):
        return False