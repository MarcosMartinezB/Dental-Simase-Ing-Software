from django.urls import path

from . import views

urlpatterns = [
    path('pagos/', views.cobros, name='cobros'),
    path('pagos/cita/<int:cita_id>/', views.registrar_pago, name='registrar_pago'),
    path('pagos/<int:pk>/comprobante/', views.comprobante, name='comprobante'),
]
