from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, RolUsuario

@admin.register(RolUsuario)
class RolUsuarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'activo', 'creado_en')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion')

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    # Columnas visibles en la tabla principal del Admin
    list_display = ('username', 'rut', 'email', 'first_name', 'last_name', 'rol', 'activo', 'is_staff')
    list_filter = ('rol', 'activo', 'is_staff', 'is_superuser')
    search_fields = ('username', 'rut', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    # Secciones adicionales en el formulario de edición
    fieldsets = UserAdmin.fieldsets + (
        ('Información Clínica y Datos Personales', {
            'fields': ('rut', 'telefono', 'rol', 'activo')
        }),
    )
    
    # Secciones adicionales en el formulario de creación de nuevo usuario
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Datos del Sistema Simase', {
            'fields': ('rut', 'email', 'first_name', 'last_name', 'telefono', 'rol')
        }),
    )
