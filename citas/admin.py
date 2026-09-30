from django.contrib import admin
from .models import CitaMedica

@admin.register(CitaMedica)
class CitaMedicaAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora', 'paciente', 'odontologo', 'estado', 'activo')
    list_filter = ('estado', 'fecha_hora', 'activo')
    search_fields = ('paciente__rut', 'paciente__nombres', 'paciente__apellidos', 'odontologo__username')
    ordering = ('fecha_hora',)