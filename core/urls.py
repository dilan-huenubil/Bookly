from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path('', index, name='index'),
    path('libros/<str:sku>/', libro_detalles, name='libro_detalles'),
    path('register/', register, name='register'),
    path('login/', register, name='login'),
    path('logout/', logout_view, name='logout'),
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
]