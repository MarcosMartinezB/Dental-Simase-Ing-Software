from django.db import models

class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(activo=False)

    def hard_delete(self):
        return super().delete()

    def vivos(self):
        return self.filter(activo=True)

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(activo=True)

    def todos_con_eliminados(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

class SoftDeleteModel(models.Model):
    """
    Modelo base abstracto para Soft Delete y auditoría básica.
    Garantiza la intangibilidad de registros en la base de datos.
    """
    activo = models.BooleanField(default=True, verbose_name="Activo")
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    modificado_en = models.DateTimeField(auto_now=True, verbose_name="Última Modificación")

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.activo = False
        self.save(using=using)

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)