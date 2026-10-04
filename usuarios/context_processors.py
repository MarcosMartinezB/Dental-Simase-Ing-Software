from django.urls import NoReverseMatch, reverse

from .models import RolUsuario

# Para agregar una pantalla al menú basta con añadir una línea:
# (texto que se ve, nombre de la URL). Si esa URL aún no existe, se omite.
MENU_POR_ROL = {
    RolUsuario.RECEPCIONISTA: [
        ('Inicio', 'panel'),
        ('Registrar paciente', 'registrar_paciente'),
        ('Agendar cita', 'agendar_cita'),
        ('Agenda del día', 'agenda_dia'),
        ('Registrar pago', 'registrar_pago'),
    ],
    RolUsuario.PACIENTE: [
        ('Inicio', 'panel'),
        ('Reservar cita', 'reservar_cita'),
        ('Mis citas', 'mis_citas'),
        ('Cambiar contraseña', 'cambiar_password'),
    ],
    RolUsuario.ODONTOLOGO: [
        ('Inicio', 'panel'),
        ('Mis citas', 'citas_odontologo'),
        ('Fichas clínicas', 'fichas'),
        ('Registrar atención', 'registrar_atencion'),
        ('Cambiar contraseña', 'cambiar_password'),
    ],
    RolUsuario.INVENTARIO: [
        ('Inicio', 'panel'),
        ('Stock', 'stock'),
        ('Registrar movimiento', 'registrar_movimiento'),
    ],
    RolUsuario.ADMINISTRADOR: [
        ('Inicio', 'panel'),
        ('Usuarios', 'gestionar_usuarios'),
        ('Aranceles', 'aranceles'),
        ('Reportes', 'reportes'),
    ],
}


def menu(request):
    usuario = request.user
    if not usuario.is_authenticated:
        return {}

    items = []
    for etiqueta, nombre in MENU_POR_ROL.get(usuario.rol, []):
        try:
            url = reverse(nombre)
        except NoReverseMatch:
            continue  # la pantalla todavía no está construida
        items.append({'etiqueta': etiqueta, 'url': url, 'activo': request.path == url})

    if usuario.is_superuser:
        items.append({'etiqueta': 'Admin de Django', 'url': reverse('admin:index'),
                      'activo': False})
    return {'menu_items': items}
