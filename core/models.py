from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist


class Book(models.Model):
	title = models.CharField("Título", max_length=255)
	author = models.CharField("Autor", max_length=255)
	editorial = models.CharField("Editorial", max_length=255, blank=True, null=True)
	binding = models.CharField("Encuadernación", max_length=100, blank=True, null=True)
	sku = models.CharField("SKU", max_length=64, unique=True)
	category = models.CharField("Categoría", max_length=255, blank=True, null=True)
	tags = models.CharField("Etiquetas (separadas por coma)", max_length=255, blank=True, null=True)
	description = models.TextField("Descripción", blank=True, null=True)
	price = models.IntegerField("Precio")
	price_old = models.IntegerField("Precio anterior", blank=True, null=True)
	discount_percent = models.IntegerField("Descuento (%)", blank=True, null=True)
	stock = models.IntegerField("Stock", default=0)
	weight_kg = models.DecimalField("Peso (kg)", max_digits=6, decimal_places=3, blank=True, null=True)
	dimensions = models.CharField("Dimensiones", max_length=100, blank=True, null=True)
	year = models.IntegerField("Año de edición", blank=True, null=True)
	pages = models.IntegerField("Páginas", blank=True, null=True)
	language = models.CharField("Idioma", max_length=64, blank=True, null=True)
	image_url = models.URLField("Imagen (URL)", blank=True, null=True)
	created_at = models.DateTimeField("Creado el", auto_now_add=True)
	updated_at = models.DateTimeField("Actualizado el", auto_now=True)

	def __str__(self):
		return f"{self.title} ({self.sku})"


class Order(models.Model):
    STATUS_CHOICES = (
        ('created', 'Creada'),
        ('paid', 'Pagada'),
        ('canceled', 'Cancelada'),
        ('error', 'Error'),
    )

    TRACKING_CHOICES = (
        ('preparando', 'Preparando Pedido'),
        ('en_camino', 'En Camino'),
        ('entregado', 'Entregado'),
    )

    user = models.ForeignKey(User, verbose_name="Usuario", on_delete=models.CASCADE, related_name='orders')
    commerce_order = models.CharField("Orden de comercio", max_length=64, unique=True)
    flow_token = models.CharField("Token Flow", max_length=128, blank=True, null=True)
    flow_order = models.CharField("Orden Flow", max_length=64, blank=True, null=True)
    amount = models.IntegerField("Monto")
    currency = models.CharField("Moneda", max_length=8, default='CLP')
    email = models.EmailField("Email comprador")
    coupon_code = models.CharField("Cupón aplicado", max_length=50, blank=True, null=True)
    shipping_name = models.CharField("Nombre receptor", max_length=128, blank=True, null=True)
    shipping_phone = models.CharField("Teléfono receptor", max_length=32, blank=True, null=True)
    shipping_line1 = models.CharField("Dirección (calle y número)", max_length=128, blank=True, null=True)
    shipping_line2 = models.CharField("Depto / bloque (opcional)", max_length=128, blank=True, null=True)
    first_item_title = models.CharField(max_length=255, null=True, blank=True)
    shipping_comuna = models.CharField("Comuna", max_length=64, blank=True, null=True)
    shipping_region = models.CharField("Región", max_length=64, blank=True, null=True)
    shipping_postal_code = models.CharField("Código postal", max_length=16, blank=True, null=True)
    status = models.CharField("Estado", max_length=16, choices=STATUS_CHOICES, default='created')
    tracking_status = models.CharField("Estado de seguimiento", max_length=20, choices=TRACKING_CHOICES, default='preparando')
    estimated_delivery_date = models.DateField("Fecha estimada de entrega", blank=True, null=True)
    created_at = models.DateTimeField("Creado el", auto_now_add=True)
    updated_at = models.DateTimeField("Actualizado el", auto_now=True)

    def __str__(self):
        return f"Order {self.commerce_order} ({self.status})"


class OrderItem(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Orden")
	book = models.ForeignKey(Book, on_delete=models.PROTECT, verbose_name="Libro")
	quantity = models.PositiveIntegerField("Cantidad", default=1)
	price_at_purchase = models.IntegerField("Precio al momento de compra")

	def __str__(self):
		return f"{self.quantity} x {self.book.title} (Orden: {self.order.commerce_order})"


class CouponRedemption(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coupon_redemptions')
	code = models.CharField(max_length=50)
	used_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('user', 'code')

	def __str__(self):
		return f"{self.user.username} - {self.code} ({self.used_at})"

class Address(models.Model):
	ADDRESS_TYPES = (
		('shipping', 'Despacho'),
		('billing', 'Cobranza'),
	)

	user = models.ForeignKey(User, verbose_name="Usuario", on_delete=models.CASCADE, related_name='addresses')
	address_type = models.CharField("Tipo de dirección", max_length=16, choices=ADDRESS_TYPES, default='shipping')
	name = models.CharField("Nombre receptor", max_length=128)
	phone = models.CharField("Teléfono", max_length=32)
	line1 = models.CharField("Dirección (calle y número)", max_length=128)
	line2 = models.CharField("Depto / bloque (opcional)", max_length=128, blank=True, null=True)
	comuna = models.CharField("Comuna", max_length=64)
	region = models.CharField("Región", max_length=64)
	postal_code = models.CharField("Código postal", max_length=16, blank=True, null=True)
	is_default = models.BooleanField("Predeterminada", default=False)
	created_at = models.DateTimeField("Creado el", auto_now_add=True)
	updated_at = models.DateTimeField("Actualizado el", auto_now=True)

	def __str__(self):
		return f"{self.user.username} - {self.address_type} ({self.line1}, {self.comuna})"




class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Usuario")
    phone = models.CharField("Teléfono", max_length=32, blank=True, null=True)
    rut = models.CharField("RUT", max_length=20, blank=True, null=True)
    doc_type = models.CharField("Tipo de documento", max_length=20, default='RUT')

    def __str__(self):
        return f"Perfil de {self.user.username}"

# Estas señales aseguran que cada vez que se cree un User nuevo, 
# se cree automáticamente su Profile asociado en blanco.
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except ObjectDoesNotExist:
        # Si el usuario es antiguo y lanza error porque no tiene perfil, lo crea aquí
        Profile.objects.create(user=instance)