from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import Cita


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora', 'paciente', 'odontologo', 'estado')
    list_filter = ('estado', 'fecha_hora')
    search_fields = (
        'paciente__rut',
        'paciente__usuario__first_name',
        'paciente__usuario__last_name',
        'odontologo__usuario__username',
    )
    ordering = ('fecha_hora',)
    actions = ['confirmar_citas', 'cancelar_citas']

    @admin.action(description='Confirmar citas seleccionadas')
    def confirmar_citas(self, request, queryset):
        self._aplicar(request, queryset, 'confirmar')

    @admin.action(description='Cancelar citas seleccionadas')
    def cancelar_citas(self, request, queryset):
        self._aplicar(request, queryset, 'cancelar')

    def _aplicar(self, request, queryset, metodo):
        ok = 0
        for cita in queryset:
            try:
                getattr(cita, metodo)()
                ok += 1
            except ValidationError as e:
                self.message_user(
                    request, f'{cita}: {" ".join(e.messages)}', level=messages.WARNING
                )
        if ok:
            self.message_user(request, f'{ok} cita(s) actualizada(s).')