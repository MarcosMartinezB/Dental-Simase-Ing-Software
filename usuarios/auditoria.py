from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType


def registrar(usuario, objeto, accion, mensaje):
    """
    Deja constancia de quién hizo qué y cuándo (log de auditoría), usando el
    registro de acciones que Django ya trae: aparece en el sitio de administración.
    `accion` es ADDITION, CHANGE o DELETION de django.contrib.admin.models.
    """
    LogEntry.objects.log_action(
        user_id=usuario.pk,
        content_type_id=ContentType.objects.get_for_model(objeto).pk,
        object_id=objeto.pk,
        object_repr=str(objeto)[:200],
        action_flag=accion,
        change_message=mensaje,
    )
