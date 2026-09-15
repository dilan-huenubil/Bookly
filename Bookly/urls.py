"""
URL configuration for Bookly project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from core import views as core_views

urlpatterns = [
    path('admin/libros/', core_views.admin_books, name='admin_books'),
    path('admin/libros/nuevo/', core_views.admin_book_save, name='admin_book_create'),
    path('admin/libros/<int:book_id>/editar/', core_views.admin_book_save, name='admin_book_edit'),
    path('admin/libros/<int:book_id>/estado/', core_views.admin_book_toggle, name='admin_book_toggle'),
    path('admin/libros/<int:book_id>/stock/', core_views.admin_book_stock, name='admin_book_stock'),
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]
