from django.contrib import admin

from django.contrib import admin
from .models import Paciente, AntecedenteMedico, FichaClinica

class AntecedenteMedicoInline(admin.StackedInline):
    model = AntecedenteMedico
    extra = 0

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombres', 'apellidos', 'telefono', 'email', 'activo')
    search_fields = ('rut', 'nombres', 'apellidos')
    list_filter = ('sexo', 'activo')
    inlines = [AntecedenteMedicoInline]

@admin.register(FichaClinica)
class FichaClinicaAdmin(admin.ModelAdmin):
    list_display = ('numero_ficha', 'paciente', 'fecha_apertura', 'activo')
    search_fields = ('numero_ficha', 'paciente__rut', 'paciente__nombres', 'paciente__apellidos')
    list_filter = ('activo', 'fecha_apertura')
