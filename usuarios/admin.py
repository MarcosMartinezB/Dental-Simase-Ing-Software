from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .base import SoftDeleteAdminMixin
from .models import Odontologo, Paciente, RolUsuario, Usuario


class UsuarioCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'email', 'first_name', 'last_name', 'rol')


class UsuarioChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Usuario
        fields = '__all__'


class PacienteInline(admin.StackedInline):
    model = Paciente
    can_delete = False
    max_num = 1


class OdontologoInline(admin.StackedInline):
    model = Odontologo
    can_delete = False
    max_num = 1


@admin.register(Usuario)
class UsuarioAdmin(SoftDeleteAdminMixin, UserAdmin):
    form = UsuarioChangeForm
    add_form = UsuarioCreationForm

    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'activo', 'is_staff')
    list_filter = ('rol', 'activo', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    readonly_fields = ('is_active',)  # se controla con 'activo'

    fieldsets = UserAdmin.fieldsets + (
        ('Datos del sistema Simase', {'fields': ('rol', 'activo')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Datos del sistema Simase', {
            'fields': ('email', 'first_name', 'last_name', 'rol')
        }),
    )

    def get_inlines(self, request, obj=None):
        # El perfil que corresponde según el rol (se agrega al editar el usuario).
        if obj is None:
            return []
        if obj.rol == RolUsuario.PACIENTE:
            return [PacienteInline]
        if obj.rol == RolUsuario.ODONTOLOGO:
            return [OdontologoInline]
        return []


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('rut', 'usuario', 'telefono', 'fecha_nacimiento')
    search_fields = ('rut', 'usuario__first_name', 'usuario__last_name', 'usuario__username')


@admin.register(Odontologo)
class OdontologoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'especialidad')
    search_fields = ('usuario__first_name', 'usuario__last_name', 'especialidad')