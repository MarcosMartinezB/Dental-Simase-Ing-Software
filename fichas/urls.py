from django.urls import path
from django.urls import path
 
from . import views
 
urlpatterns = [
    path('fichas/', views.fichas, name='fichas'),
    path('fichas/<int:pk>/', views.ficha_detalle, name='ficha_detalle'),
    path('atenciones/nueva/<int:cita_id>/', views.registrar_atencion, name='registrar_atencion'),
]