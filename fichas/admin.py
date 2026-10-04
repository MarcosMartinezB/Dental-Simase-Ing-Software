from django.contrib import admin

from .models import Atencion, FichaClinica, Presupuesto, Tratamiento


class TratamientoInline(admin.TabularInline):
    model = Tratamiento
    extra = 0


@admin.register(FichaClinica)
class FichaClinicaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'fecha_creacion')
    search_fields = (
        'paciente__rut',
        'paciente__usuario__first_name',
        'paciente__usuario__last_name',
    )


@admin.register(Atencion)
class AtencionAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora', 'ficha', 'cita')
    list_filter = ('fecha_hora',)
    search_fields = (
        'ficha__paciente__rut',
        'ficha__paciente__usuario__first_name',
        'ficha__paciente__usuario__last_name',
    )
    inlines = [TratamientoInline]


@admin.register(Presupuesto)
class PresupuestoAdmin(admin.ModelAdmin):
    list_display = ('atencion', 'fecha_emision', 'monto_total')
    readonly_fields = ('monto_total',)