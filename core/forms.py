from django import forms
from decimal import Decimal, ROUND_HALF_UP

from .models import Book, Order


class BookAdminForm(forms.ModelForm):
    discount_percent = forms.ChoiceField(
        label='Descuento',
        choices=(
            ('', 'Sin descuento'),
            ('10', '10%'),
            ('15', '15%'),
        ),
        required=False,
    )

    class Meta:
        model = Book
        fields = (
            'title', 'author', 'editorial', 'binding', 'sku', 'category', 'tags',
            'description', 'price', 'discount_percent', 'stock', 'is_active',
            'weight_kg', 'dimensions', 'year', 'pages', 'language', 'image_url',
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'price': forms.NumberInput(attrs={'min': 0}),
            'stock': forms.NumberInput(attrs={'min': 0}),
            'weight_kg': forms.NumberInput(attrs={'min': 0, 'step': '0.001'}),
            'year': forms.NumberInput(attrs={'min': 0}),
            'pages': forms.NumberInput(attrs={'min': 0}),
            'image_url': forms.URLInput(attrs={'placeholder': 'https://...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['stock'].required = False
            self.fields['is_active'].required = False
            self.initial['price'] = self.instance.price_old or self.instance.price
            self.initial['discount_percent'] = str(self.instance.discount_percent or '')

    def clean_title(self):
        return self.cleaned_data['title'].strip()

    def clean_author(self):
        return self.cleaned_data['author'].strip()

    def clean_sku(self):
        return self.cleaned_data['sku'].strip().upper()

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 0:
            raise forms.ValidationError('El precio no puede ser negativo.')
        return price

    def clean_stock(self):
        stock = self.cleaned_data['stock']
        if stock is None and self.instance and self.instance.pk:
            return self.instance.stock
        if stock < 0:
            raise forms.ValidationError('El stock no puede ser negativo.')
        return stock

    def save(self, commit=True):
        current_stock = self.instance.stock if self.instance and self.instance.pk else 0
        book = super().save(commit=False)
        if self.instance.pk and self.cleaned_data.get('stock') is None:
            book.stock = current_stock
        if self.instance.pk and 'is_active' not in self.data:
            book.is_active = self.instance.is_active
        original_price = self.cleaned_data['price']
        discount = int(self.cleaned_data.get('discount_percent') or 0)

        if discount:
            discounted_price = (Decimal(original_price) * (Decimal('100') - Decimal(discount)) / Decimal('100'))
            book.price = int(discounted_price.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
            book.price_old = original_price
            book.discount_percent = discount
        else:
            book.price = original_price
            book.price_old = None
            book.discount_percent = None

        if commit:
            book.save()
        return book


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('status', 'tracking_status', 'estimated_delivery_date')
        widgets = {
            'estimated_delivery_date': forms.DateInput(attrs={'type': 'date'}),
        }