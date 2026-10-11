from django.urls import path

from . import views

urlpatterns = [
    path('inventario/', views.stock, name='stock'),
    path('inventario/insumos/nuevo/', views.crear_insumo, name='crear_insumo'),
    path('inventario/movimientos/nuevo/', views.registrar_movimiento, name='registrar_movimiento'),
    path('inventario/exportar/', views.exportar_stock, name='exportar_stock'),
]
