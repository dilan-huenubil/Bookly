from django.contrib import admin
from .models import Book, Order, OrderItem, Address

class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0
	fields = ("book", "quantity", "price_at_purchase")
	readonly_fields = ("book", "quantity", "price_at_purchase")
	can_delete = False


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
	list_display = ("title", "author", "editorial", "price", "stock")
	search_fields = ("title", "author", "sku", "editorial", "category")
	list_filter = ("editorial", "binding", "language")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ("commerce_order", "user", "amount", "status", "created_at")
	search_fields = ("commerce_order", "user__username", "email")
	inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
	list_display = ("order", "book", "quantity", "price_at_purchase")
	search_fields = ("order__commerce_order", "book__title", "book__sku")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
	list_display = ("user", "name", "line1", "comuna", "region", "is_default")
	search_fields = ("user__username", "line1", "comuna", "region")

# Register your models here.
