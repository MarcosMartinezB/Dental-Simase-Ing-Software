from django.urls import path

from . import views

urlpatterns = [
    path('panel/', views.panel, name='panel'),
    path('pacientes/nuevo/', views.registrar_paciente, name='registrar_paciente'),
    path('contrasena/', views.CambiarPasswordView.as_view(), name='cambiar_password'),
    path('usuarios/', views.gestionar_usuarios, name='gestionar_usuarios'),
    path('usuarios/nuevo/<str:rol>/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/<int:pk>/estado/', views.cambiar_estado_usuario, name='cambiar_estado_usuario'),
]
