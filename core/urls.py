from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *
from . import views

urlpatterns = [
    path('', index, name='index'),
    path('libros/<str:sku>/', libro_detalles, name='libro_detalles'),
    path('register/', register, name='register'),
    path('login/', register, name='login'),
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='core/password_reset_form.html',
            email_template_name='core/password_reset_email.txt',
            html_email_template_name='core/password_reset_email.html',
            subject_template_name='core/password_reset_subject.txt',
            success_url='/password-reset/done/',
        ),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='core/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'password-reset/<uidb64>/<token>/',
        views.PasswordResetConfirmView.as_view(
            template_name='core/password_reset_confirm.html',
            success_url='/password-reset/complete/',
        ),
        name='password_reset_confirm',
    ),
    path(
        'password-reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='core/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
    path('logout/', logout_view, name='logout'),
    path('mi-cuenta/eliminar/', views.delete_account, name='delete_account'),
    path('carrito/', carrito, name='carrito'),
    path('contacto/', contacto, name='contacto'),
    path('checkout/', checkout, name='checkout'),
    path('entrega/', entrega, name='entrega'),
    path('pago/', pago, name='pago'),
    path('destacados/', destacados, name='destacados'),
    path('search/', search, name='search'),
    path('pago/create/', pago_create, name='pago_create'),
    path('flow/return/', flow_return, name='flow_return'),
    path('flow/callback/', flow_callback, name='flow_callback'),
    path('flow/debug/', flow_debug, name='flow_debug'),
    path('addresses/set-default/<int:address_id>/', set_default_address, name='set_default_address'),
    path('addresses/delete/<int:address_id>/', delete_address, name='delete_address'),
    path('confirmacion_pedido/', confirmacion_pedido, name='confirmacion_pedido'),
    path('mis_pedidos/', mis_pedidos, name='mis_pedidos'),
    path('mi-perfil/', views.mi_perfil, name='mi_perfil'),
    path('mi-contrasena/', views.mi_contrasena, name='mi_contrasena'),
    path('admin/libros/', views.admin_books, name='admin_books'),
    path('admin/libros/nuevo/', views.admin_book_save, name='admin_book_create'),
    path('admin/libros/<int:book_id>/editar/', views.admin_book_save, name='admin_book_edit'),
    path('admin/libros/<int:book_id>/estado/', views.admin_book_toggle, name='admin_book_toggle'),
    path('admin/libros/<int:book_id>/stock/', views.admin_book_stock, name='admin_book_stock'),
    path('admin/pedidos/', views.admin_orders, name='admin_orders'),
    path('admin/pedidos/<int:order_id>/editar/', views.admin_order_edit, name='admin_order_edit'),
    path('admin/pedidos/<int:order_id>/eliminar/', views.admin_order_delete, name='admin_order_delete'),
]