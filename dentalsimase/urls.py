from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from usuarios.views import panel

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', auth_views.LoginView.as_view(
        template_name='login.html',
        redirect_authenticated_user=True), name='login'),
    path('panel/', panel, name='panel'),
    path('salir/', auth_views.LogoutView.as_view(), name='logout'),
]