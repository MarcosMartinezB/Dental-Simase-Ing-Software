from django.urls import path

from . import views

urlpatterns = [
    path('citas/reservar/', views.reservar_cita, name='reservar_cita'),
    path('citas/mis-citas/', views.mis_citas, name='mis_citas'),
    path('citas/agendar/', views.agendar_cita, name='agendar_cita'),
    path('citas/agenda/', views.agenda_dia, name='agenda_dia'),
    path('citas/odontologo/', views.citas_odontologo, name='citas_odontologo'),
    path('citas/<int:pk>/', views.detalle_cita, name='detalle_cita'),
    path('citas/<int:pk>/cancelar/', views.cancelar_cita, name='cancelar_cita'),
]