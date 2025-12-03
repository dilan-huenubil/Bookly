from django.contrib import admin
from .models import Book, Order, Address


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
	list_display = ("title", "author", "editorial", "price", "stock")
	search_fields = ("title", "author", "sku", "editorial", "category")
	list_filter = ("editorial", "binding", "language")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ("commerce_order", "user", "amount", "status", "created_at")
	search_fields = ("commerce_order", "user__username", "email")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
	list_display = ("user", "name", "line1", "comuna", "region", "is_default")
	search_fields = ("user__username", "line1", "comuna", "region")

# Register your models here.
