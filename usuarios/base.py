from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return self.update(activo=False, modificado_en=timezone.now())

    def hard_delete(self):
        return super().delete()

    def vivos(self):
        return self.filter(activo=True)


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    def get_queryset(self):
        return super().get_queryset().filter(activo=True)


class TodosManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    """Incluye registros inactivos, pero sigue haciendo soft delete."""


class SoftDeleteModel(models.Model):
    """Base abstracta: baja lógica y auditoría básica (solo se usa en Usuario)."""
    activo = models.BooleanField(default=True, verbose_name="Activo")
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    modificado_en = models.DateTimeField(auto_now=True, verbose_name="Última modificación")

    objects = SoftDeleteManager()
    all_objects = TodosManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.activo = False
        self.save(using=using)

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)


class SoftDeleteAdminMixin:
    """Hace que el admin muestre también los registros inactivos."""

    def get_queryset(self, request):
        qs = self.model.all_objects.all()
        ordering = self.get_ordering(request)
        return qs.order_by(*ordering) if ordering else qs