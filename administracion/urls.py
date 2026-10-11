from django.urls import path

from . import views

urlpatterns = [
    path('administracion/aranceles/', views.aranceles, name='aranceles'),
    path('administracion/aranceles/nuevo/', views.crear_arancel, name='crear_arancel'),
    path('administracion/aranceles/<int:pk>/editar/', views.editar_arancel, name='editar_arancel'),
    path('administracion/reportes/', views.reportes_gestion, name='reportes'),
    path('administracion/reportes/pdf/', views.reporte_pdf, name='reporte_pdf'),
    path('administracion/reportes/correo/', views.reporte_correo, name='reporte_correo'),
]
