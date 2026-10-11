from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def rol_requerido(*roles):
    """Restringe una vista a ciertos roles. Sin sesión -> login; rol distinto -> 403."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.rol not in roles:
                raise PermissionDenied
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador
