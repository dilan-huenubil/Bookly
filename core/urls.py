from django.urls import path

from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('libros/<slug:sku>/', libro_detalles, name='libro_detalles'),
    path('register/', register, name='register'),
    path('carrito/', carrito, name='carrito'),
    path('contacto/', contacto, name='contacto'),
    path('logout/', logout_view, name='logout'),
    path('checkout/', checkout, name='checkout'),
    path('entrega/', entrega, name='entrega'),
    path('pago/', pago, name='pago'),
    path('destacados/', destacados, name='destacados'),
    path('pago/create/', pago_create, name='pago_create'),
    path('addresses/set-default/<int:address_id>/', set_default_address, name='set_default_address'),
    # Flow payment endpoints (sandbox)
    path('flow/return/', flow_return, name='flow_return'),
    path('flow/callback/', flow_callback, name='flow_callback'),
    path('flow/debug/', flow_debug, name='flow_debug'),
    # Addresses management
    path('addresses/delete/<int:address_id>/', delete_address, name='delete_address'),
    path('confirmacion_pedido/', confirmacion_pedido, name='confirmacion_pedido'),
]