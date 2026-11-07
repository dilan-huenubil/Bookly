from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.db import IntegrityError, transaction
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Max, Q
import re
import hmac
import hashlib
import requests
import time
import uuid
import json
from html.parser import HTMLParser
from html import unescape
from urllib.parse import urlparse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import update_session_auth_hash, views as auth_views
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from functools import wraps

from .models import (
    Order,
    OrderItem,
    Address,
    Book,
    CouponRedemption,
    Profile,
)
from .forms import BookAdminForm, OrderAdminForm
from django.core.paginator import Paginator

# Create your views here.

ORDER_PAYMENT_TIMEOUT = timedelta(minutes=15)
COUPON_DISCOUNTS = {'bookly10': 10, 'bookly15': 15}


class FeriaBookParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.text_parts = []
        self.image_url = ''
        self.heading = ''
        self.in_heading = False
        self.in_json_ld = False
        self.json_ld = ''

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('property', '').startswith('og:'):
            self.meta[attrs['property']] = attrs.get('content', '').strip()
        if tag == 'img' and not self.image_url and attrs.get('class', '').find('wp-post-image') >= 0:
            self.image_url = attrs.get('src', '')
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.in_json_ld = True
        if tag == 'h1':
            self.in_heading = True

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_json_ld = False
        if tag == 'h1':
            self.in_heading = False

    def handle_data(self, data):
        if self.in_heading and not self.heading:
            self.heading = ' '.join(data.split())
        if self.in_json_ld:
            self.json_ld += data
        else:
            text = ' '.join(data.split())
            if text:
                self.text_parts.append(text)


def _feria_number(value):
    match = re.search(r'[\d.]+', value or '')
    return int(match.group(0).replace('.', '')) if match else None


def _feria_book_data(url):
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or parsed.netloc.lower() != 'feriachilenadellibro.cl':
        raise ValueError('La URL debe pertenecer a feriachilenadellibro.cl.')

    response = requests.get(
        url,
        headers={'User-Agent': 'Bookly inventory importer'},
        timeout=10,
    )
    response.raise_for_status()
    response.encoding = 'utf-8'
    parser = FeriaBookParser()
    parser.feed(response.text)
    text = ' '.join(parser.text_parts)
    title = parser.heading or parser.meta.get('og:title', '')
    if not title:
        title_match = re.search(r'(?<!Autor: )(?<!/ )([A-ZÁÉÍÓÚÑ][^|]{2,100}) Autor:', text)
        title = title_match.group(1).strip() if title_match else ''

    def field(label, next_label):
        match = re.search(
            rf'{re.escape(label)}:\s*(.*?)(?=\s+{re.escape(next_label)}:)',
            text,
            re.IGNORECASE,
        )
        return match.group(1).strip() if match else ''

    sku_match = re.search(r'(?:SKU|ISBN):\s*([0-9X-]{10,17})', text, re.IGNORECASE)
    if not sku_match:
        sku_match = re.search(r'/producto/([0-9X-]+)-', url, re.IGNORECASE)
    price_match = re.search(r'Precio Internet:\s*\$?\s*([\d.]+)', text, re.IGNORECASE)
    description_match = re.search(
        r'id=["\']tab-description["\'][^>]*>(.*?)(?=</div>\s*<div[^>]+id=["\']tab-additional_information["\'])',
        response.text,
        re.IGNORECASE | re.DOTALL,
    )
    description = ''
    if description_match:
        description = re.sub(r'<[^>]+>', ' ', description_match.group(1))
        description = re.sub(r'\s+', ' ', unescape(description)).strip()
        if title and description.casefold().startswith(title.casefold()):
            description = description[len(title):].lstrip(' .:-')
        description = re.split(r'\s+Adquiera\s+', description, maxsplit=1, flags=re.IGNORECASE)[0].strip()
    if not description:
        description = parser.meta.get('og:description', '')
    data = {
        'title': title,
        'author': field('Autor', 'Editorial'),
        'editorial': field('Editorial', 'Encuadernación'),
        'binding': field('Encuadernación', 'Precio Internet'),
        'sku': sku_match.group(1).replace('-', '').upper() if sku_match else '',
        'price': int(price_match.group(1).replace('.', '')) if price_match else None,
        'description': description,
        'image_url': parser.meta.get('og:image', '') or parser.image_url,
    }
    def attribute_value(attribute):
        match = re.search(
            rf'product-attributes-item--{attribute}[^>]*>.*?'
            r'woocommerce-product-attributes-item__value[^>]*>(.*?)</td>',
            response.text,
            re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return ''
        value = re.sub(r'<[^>]+>', ' ', unescape(match.group(1)))
        return re.sub(r'\s+', ' ', value).strip()

    weight = attribute_value('weight')
    dimensions = attribute_value('dimensions')
    language = attribute_value('attribute_pa_idioma')
    pages = attribute_value('attribute_pa_paginas')
    year = attribute_value('attribute_pa_ano-edicion')
    if weight:
        data['weight_kg'] = weight.replace(' kg', '').replace(',', '.').strip()
    if dimensions:
        data['dimensions'] = dimensions.replace('×', 'x').strip()
    if language:
        data['language'] = language
    if pages:
        data['pages'] = pages
    if year:
        data['year'] = year
    category_html = re.search(
        r'<span[^>]+class=["\'][^"\']*posted_in[^"\']*["\'][^>]*>(.*?)</span>',
        response.text,
        re.IGNORECASE | re.DOTALL,
    )
    if category_html:
        category_links = re.findall(
            r'<a[^>]*>(.*?)</a>',
            category_html.group(1),
            re.IGNORECASE | re.DOTALL,
        )
        categories = [
            re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', '', value))).strip()
            for value in category_links
        ]
        if categories:
            data['category'] = categories[-1]

    tags_html = re.search(
        r'<span[^>]+class=["\'][^"\']*tagged_as[^"\']*["\'][^>]*>(.*?)</span>',
        response.text,
        re.IGNORECASE | re.DOTALL,
    )
    if tags_html:
        tag_links = re.findall(
            r'<a[^>]*>(.*?)</a>',
            tags_html.group(1),
            re.IGNORECASE | re.DOTALL,
        )
        tags = [
            re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', '', value))).strip()
            for value in tag_links
        ]
        if tags:
            data['tags'] = ', '.join(tags)
    return data


def send_password_changed_email(user):
    context = {'user': user}
    text_body = render_to_string(
        'core/password_changed_email.txt',
        context,
    )
    html_body = render_to_string(
        'core/password_changed_email.html',
        context,
    )
    email = EmailMultiAlternatives(
        subject='Tu contraseña de Bookly fue actualizada',
        body=text_body,
        to=[user.email],
    )
    email.attach_alternative(html_body, 'text/html')
    email.send(fail_silently=False)


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    def form_valid(self, form):
        response = super().form_valid(form)
        send_password_changed_email(self.user)
        return response


def coupon_was_used(user, code):
    return (
        CouponRedemption.objects.filter(user=user, code__iexact=code).exists() or
        Order.objects.filter(user=user, coupon_code__iexact=code).exists()
    )


def cancel_expired_orders(user=None):
    expiration_time = timezone.now() - ORDER_PAYMENT_TIMEOUT
    expired_orders = Order.objects.filter(
        status='created',
        confirmation_reached=False,
        created_at__lt=expiration_time,
    )
    if user is not None:
        expired_orders = expired_orders.filter(user=user)
    return expired_orders.update(status='canceled', updated_at=timezone.now())

def index(request):
    books = Book.objects.filter(is_active=True).order_by('-created_at')
    price_filter = request.GET.get('price', 'all')
    price_filters = {
        '0-15000': {'price__lte': 15000},
        '15000-30000': {'price__gt': 15000, 'price__lte': 30000},
        '30000-60000': {'price__gt': 30000, 'price__lte': 60000},
        '60000-plus': {'price__gt': 60000},
    }
    if price_filter not in price_filters and price_filter != 'all':
        price_filter = 'all'
    if price_filter in price_filters:
        books = books.filter(**price_filters[price_filter])
    books_paginator = Paginator(books, 15)
    books_page = books_paginator.get_page(request.GET.get('page'))
    pagination_window = 15
    pagination_start = max(1, books_page.number - pagination_window // 2)
    pagination_end = min(
        books_paginator.num_pages,
        pagination_start + pagination_window - 1,
    )
    pagination_start = max(1, pagination_end - pagination_window + 1)
    pagination_page_numbers = range(pagination_start, pagination_end + 1)
    recommendations = []
    section_title = 'Los libros más vendidos'

    if request.user.is_authenticated:
        purchased_book_ids = OrderItem.objects.filter(
            order__user=request.user,
            order__status='paid',
        ).values_list('book_id', flat=True)

        if purchased_book_ids.exists():
            section_title = 'Basado en tus compras recientes'
            purchased_categories = Book.objects.filter(
                pk__in=purchased_book_ids,
            ).values_list('category', flat=True).distinct()

            recommendations = list(
                Book.objects.filter(
                    recommendations_to__book_id__in=purchased_book_ids,
                    category__in=purchased_categories,
                    is_active=True,
                    stock__gt=0,
                )
                .exclude(pk__in=purchased_book_ids)
                .annotate(recommendation_score=Max('recommendations_to__score'))
                .distinct()
                .order_by('-recommendation_score', '-created_at')[:6]
            )

            if len(recommendations) < 6:
                excluded_book_ids = list(purchased_book_ids) + [
                    book.pk for book in recommendations
                ]
                recommendations.extend(
                    Book.objects.filter(
                        category__in=purchased_categories,
                        is_active=True,
                        stock__gt=0,
                    )
                    .exclude(pk__in=excluded_book_ids)
                    .annotate(
                        total_vendidos=Count(
                            'orderitem',
                            filter=Q(orderitem__order__status='paid'),
                        )
                    )
                    .order_by('-total_vendidos', '-created_at')[
                        :6 - len(recommendations)
                    ]
                )

    if not recommendations:
        section_title = 'Los libros más vendidos'
        recommendations = list(
            Book.objects.filter(
                is_active=True,
                stock__gt=0,
            )
            .annotate(
                total_vendidos=Count(
                    'orderitem',
                    filter=Q(orderitem__order__status='paid'),
                )
            )
            .order_by('-total_vendidos', '-created_at')[:6]
        )

    return render(request, 'core/index.html', {
        'books': books_page,
        'recommendations': recommendations,
        'section_title': section_title,
        'price_filter': price_filter,
        'pagination_page_numbers': pagination_page_numbers,
    })

def libro_detalles(request, sku: str):
    book = get_object_or_404(Book, sku=sku, is_active=True)
    tags_list = []
    if book.tags:
        tags_list = [t.strip() for t in book.tags.split(',') if t.strip()]
    related_books = []
    if book.category:
        related_books = Book.objects.filter(category=book.category).exclude(pk=book.pk)[:4]
    context = {
        'book': book,
        'tags_list': tags_list,
        'related_books': related_books,
    }
    return render(request, 'core/detalles.html', context)


def register(request):
    if request.method == 'GET':
        return render(request, 'core/register-login.html', {
            'login_error': '',
            'register_error': '',
            'success': ''
        })

    form_type = request.POST.get('form_type')

    # REGISTRO
    if form_type == "register":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Validaciones importantes del servidor
        if User.objects.filter(email=email).exists():
            return render(request, 'core/register-login.html', {
                'register_error': 'El correo ya está registrado',
                'login_error': ''
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'core/register-login.html', {
                'register_error': 'El nombre de usuario ya existe',
                'login_error': ''
            })

        if password1 != password2:
            return render(request, 'core/register-login.html', {
                'register_error': 'Las contraseñas no coinciden',
                'login_error': ''
            })

        # Validación de contraseña segura
        if (
            len(password1) < 8 or
            not re.search(r"[A-Z]", password1) or
            not re.search(r"[\W_]", password1)
        ):
            return render(request, 'core/register-login.html', {
                'register_error': 'La contraseña debe tener mínimo 8 caracteres, una mayúscula y un símbolo.',
                'login_error': ''
            })

        # Crear usuario
        User.objects.create_user(
            username=username,
            password=password1,
            email=email
        )

        return render(request, 'core/register-login.html', {
            'success': 'Usuario creado correctamente. Ahora puedes iniciar sesión.',
            'register_error': '',
            'login_error': ''
        })

    # LOGIN
    elif form_type == "login":
        identifier = request.POST.get('username')
        password = request.POST.get('password')

        next_url = request.POST.get('next') or request.GET.get('next')

        user = authenticate(request, username=identifier, password=password)

        if user is None:
            return render(request, 'core/register-login.html', {
                'login_error': 'Usuario o contraseña incorrectos',
                'register_error': ''
            })

        login(request, user)
        profile = getattr(user, 'profile', None)
        if profile and profile.deletion_requested_at is not None:
            profile.deletion_requested_at = None
            profile.save(update_fields=['deletion_requested_at'])
            messages.success(request, 'Tu cuenta fue recuperada correctamente.')

        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()}
        ):
            return redirect(next_url)

        return redirect('index')


@login_required
def carrito(request):
    return render(request, 'core/carrito.html')

def contacto(request):
    return render(request, 'core/contacto.html')


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
        is_admin = request.user.is_superuser or request.user.is_staff
        try:
            is_admin = is_admin or request.user.profile.role == 'admin'
        except ObjectDoesNotExist:
            pass
        if not is_admin:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapped


@login_required
@admin_required
def admin_books(request):
    query = request.GET.get('q', '').strip()
    books = Book.objects.all().order_by('-is_active', '-updated_at')
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(sku__icontains=query) |
            Q(category__icontains=query)
        )
    return render(request, 'core/admin_books.html', {
        'books': books,
        'form': BookAdminForm(),
        'query': query,
    })


@login_required
@admin_required
def admin_book_import(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido.'}, status=405)
    url = request.POST.get('url', '').strip()
    if not url:
        return JsonResponse({'error': 'Ingresa la URL de una ficha de producto.'}, status=400)
    try:
        data = _feria_book_data(url)
    except (ValueError, requests.RequestException) as error:
        return JsonResponse({'error': str(error)}, status=400)
    if not data.get('title') or not data.get('sku'):
        return JsonResponse({'error': 'No se pudo identificar el título o ISBN del libro.'}, status=422)
    return JsonResponse(data)


@login_required
@admin_required
def admin_book_save(request, book_id=None):
    book = get_object_or_404(Book, pk=book_id) if book_id else None

    if request.method == 'GET':
        return render(request, 'core/admin_books.html', {
            'books': Book.objects.all().order_by('-is_active', '-updated_at'),
            'form': BookAdminForm(instance=book),
            'editing_book': book,
            'query': '',
        })

    if request.method != 'POST':
        return redirect('admin_books')

    form = BookAdminForm(request.POST, instance=book)
    if form.is_valid():
        form.save()
        messages.success(request, 'Libro guardado correctamente.')
        return redirect('admin_books')
    return render(request, 'core/admin_books.html', {
        'books': Book.objects.all().order_by('-is_active', '-updated_at'),
        'form': form,
        'editing_book': book,
        'query': '',
    }, status=400)


@login_required
@admin_required
def admin_book_toggle(request, book_id):
    if request.method != 'POST':
        return redirect('admin_books')
    book = get_object_or_404(Book, pk=book_id)
    book.is_active = not book.is_active
    book.save(update_fields=['is_active', 'updated_at'])
    messages.success(request, 'Estado del libro actualizado.')
    return redirect('admin_books')


@login_required
@admin_required
def admin_book_stock(request, book_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido.'}, status=405)
    book = get_object_or_404(Book, pk=book_id)
    try:
        stock = int(request.POST.get('stock', ''))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'El stock debe ser un número entero.'}, status=400)
    if stock < 0:
        return JsonResponse({'error': 'El stock no puede ser negativo.'}, status=400)
    book.stock = stock
    book.save(update_fields=['stock', 'updated_at'])
    return JsonResponse({'stock': book.stock})


@login_required
@admin_required
def admin_orders(request):
    query = request.GET.get('q', '').strip()
    orders = Order.objects.select_related('user').prefetch_related('items__book').order_by('-created_at')
    if query:
        orders = orders.filter(
            Q(commerce_order__icontains=query) |
            Q(first_item_title__icontains=query) |
            Q(email__icontains=query) |
            Q(user__username__icontains=query)
        )
    return render(request, 'core/admin_orders.html', {
        'orders': orders,
        'query': query,
        'form': OrderAdminForm(),
    })


@login_required
@admin_required
def admin_order_edit(request, order_id):
    order = get_object_or_404(Order.objects.select_related('user'), pk=order_id)
    if request.method == 'GET':
        return render(request, 'core/admin_orders.html', {
            'orders': Order.objects.select_related('user').prefetch_related('items__book').order_by('-created_at'),
            'query': '',
            'form': OrderAdminForm(instance=order),
            'editing_order': order,
        })
    if request.method != 'POST':
        return redirect('admin_orders')
    form = OrderAdminForm(request.POST, instance=order)
    if form.is_valid():
        form.save()
        messages.success(request, 'Pedido actualizado correctamente.')
        return redirect('admin_orders')
    return render(request, 'core/admin_orders.html', {
        'orders': Order.objects.select_related('user').prefetch_related('items__book').order_by('-created_at'),
        'query': '',
        'form': form,
        'editing_order': order,
    }, status=400)


@login_required
@admin_required
def admin_order_delete(request, order_id):
    if request.method != 'POST':
        return redirect('admin_orders')
    order = get_object_or_404(Order, pk=order_id)
    order.delete()
    messages.success(request, 'Pedido eliminado correctamente.')
    return redirect('admin_orders')


def logout_view(request):
    logout(request)
    return redirect('index')


@login_required
def delete_account(request):
    if request.method != 'POST':
        return redirect('mi_perfil')

    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.deletion_requested_at = timezone.now()
    profile.save(update_fields=['deletion_requested_at'])
    logout(request)
    messages.success(
        request,
        'Tu cuenta se eliminará definitivamente en 30 días. '
        'Inicia sesión antes de esa fecha para recuperarla.',
    )
    return redirect('index')


@login_required
def checkout(request):
    user = request.user

    if request.method == 'POST':
        action = request.POST.get('action', 'save_address')

        if action == 'save_address':
            addr_id = request.POST.get('address_id')
            name = (request.POST.get('name') or '').strip()
            phone = (request.POST.get('phone') or '').strip()
            street = (request.POST.get('street') or '').strip()
            number = (request.POST.get('number') or '').strip()
            line2 = (request.POST.get('line2') or '').strip()
            region = (request.POST.get('region') or '').strip()
            comuna = (request.POST.get('comuna') or '').strip()
            postal_code = (request.POST.get('postal_code') or '').strip()
            make_default = request.POST.get('is_default') == 'on'

            line1 = f"{street} {number}".strip()

            if addr_id:
                try:
                    addr = Address.objects.get(id=addr_id, user=user, address_type='shipping')
                except Address.DoesNotExist:
                    addr = Address(user=user, address_type='shipping')
            else:
                addr = Address(user=user, address_type='shipping')

            addr.name = name or addr.name or user.get_full_name() or user.username
            addr.phone = phone or addr.phone or ''
            addr.line1 = line1 or addr.line1 or ''
            addr.line2 = line2 or ''
            addr.region = region or addr.region or ''
            addr.comuna = comuna or addr.comuna or ''
            addr.postal_code = postal_code or addr.postal_code or ''
            addr.save()

            if make_default:
                Address.objects.filter(user=user, address_type='shipping', is_default=True).exclude(id=addr.id).update(is_default=False)
                addr.is_default = True
                addr.save(update_fields=['is_default'])

            return redirect('checkout')

        elif action == 'save_user':
            first_name = (request.POST.get('first_name') or '').strip()
            last_name = (request.POST.get('last_name') or '').strip()
            phone = (request.POST.get('phone') or '').strip()
            email = (request.POST.get('email') or '').strip()
            rut = (request.POST.get('rut') or '').strip()
            doc_type = (request.POST.get('doc_type') or 'RUT').strip() 

            # 1. Guardar datos nativos del User
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if email:
                user.email = email
            user.save()

            # 2. Guardar datos extendidos en Profile (Creándolo si no existe)
            try:
                perfil = user.profile
            except ObjectDoesNotExist:
                perfil = Profile.objects.create(user=user)

            if rut:
                perfil.rut = rut
            if phone:
                perfil.phone = phone
            if doc_type:
                perfil.doc_type = doc_type
            perfil.save()

            # 3. Mantener sincronizado el teléfono en la dirección de envío por defecto
            if phone:
                default_addr = Address.objects.filter(user=user, address_type='shipping', is_default=True).first()
                if default_addr:
                    default_addr.phone = phone
                    default_addr.save(update_fields=['phone'])

            return redirect('checkout')

    coupon_already_used = coupon_was_used(user, 'Bookly10')
    coupon15_already_used = coupon_was_used(user, 'Bookly15')

    addresses = Address.objects.filter(user=user, address_type='shipping').order_by('-is_default', '-updated_at')
    default_address = addresses.filter(is_default=True).first() or addresses.first()

    default_street = ''
    default_number = ''
    if default_address and default_address.line1:
        parts = default_address.line1.rsplit(' ', 1)
        if len(parts) == 2 and parts[1].isdigit():
            default_street, default_number = parts[0], parts[1]
        else:
            default_street = default_address.line1

    has_addresses = addresses.exists()

    # Extraer teléfono y RUT directamente desde el perfil (Consultándolo de forma segura)
    user_phone = ''
    user_rut = ''
    try:
        user_phone = user.profile.phone or ''
        user_rut = user.profile.rut or ''
    except ObjectDoesNotExist:
        pass

    # Respaldo: si el perfil no tiene teléfono, buscar en la dirección por defecto
    if not user_phone and default_address:
        user_phone = default_address.phone or ''

    has_user_data = bool(
        (user.first_name or '').strip() and
        (user.last_name or '').strip() and
        (user.email or '').strip() and
        (user_phone or '').strip()
    )

    context = {
        'user': user,
        'addresses': addresses,
        'default_address': default_address,
        'has_addresses': has_addresses,
        'user_phone': user_phone,
        'user_rut': user_rut, 
        'default_street': default_street,
        'default_number': default_number,
        'show_shipping': False,
        'has_user_data': has_user_data,
        'can_continue': has_user_data and has_addresses,
        'coupon_already_used': coupon_already_used,
        'coupon15_already_used': coupon15_already_used,
    }
    return render(request, 'core/checkout.html', context)

@login_required
def entrega(request):
    addresses = Address.objects.filter(user=request.user, address_type='shipping')
    default_address = addresses.filter(is_default=True).first() or addresses.first()
    has_addresses = addresses.exists()
    user_phone = (default_address.phone if default_address else '')
    has_user_data = bool(
        (request.user.first_name or '').strip() and
        (request.user.last_name or '').strip() and
        (request.user.email or '').strip() and
        (user_phone or '').strip()
    )
    if not (has_addresses and has_user_data):
        return redirect('checkout')

    coupon_already_used = coupon_was_used(request.user, 'Bookly10')
    coupon15_already_used = coupon_was_used(request.user, 'Bookly15')

    sku = request.GET.get('sku')
    book = None
    if sku:
        try:
            book = Book.objects.get(sku=sku, is_active=True)
        except Book.DoesNotExist:
            book = None
    context = {
        'book': book,
        'show_shipping': True,
        'coupon_already_used': coupon_already_used,
        'coupon15_already_used': coupon15_already_used,
    }
    return render(request, 'core/entrega.html', context)


@login_required
def pago(request):
    sku = request.GET.get('sku')
    book = None
    if sku:
        try:
            book = Book.objects.get(sku=sku, is_active=True)
        except Book.DoesNotExist:
            book = None

    coupon_already_used = coupon_was_used(request.user, 'Bookly10')
    coupon15_already_used = coupon_was_used(request.user, 'Bookly15')

    return render(request, 'core/pago.html', {
        'book': book,
        'show_shipping': True,
        'coupon_already_used': coupon_already_used,
        'coupon15_already_used': coupon15_already_used,
    })



def _flow_string_to_sign(params: dict) -> str:
    items = sorted((k, str(v)) for k, v in params.items() if k != 's')
    return '&'.join(f"{k}={v}" for k, v in items)

def _flow_sign(params: dict, secret: str) -> str:
    data = _flow_string_to_sign(params)
    return hmac.new(secret.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()


def _parse_cart_payload(request):
    raw_cart = request.GET.get('cart') or request.POST.get('cart')

    if not raw_cart and request.content_type and 'application/json' in request.content_type:
        try:
            body = json.loads(request.body.decode('utf-8') or '{}')
        except Exception:
            body = {}
        if isinstance(body, dict):
            raw_cart = body.get('cart') or body.get('carrito')

    if not raw_cart:
        return []

    if isinstance(raw_cart, list):
        return raw_cart

    if isinstance(raw_cart, dict):
        return raw_cart.get('cart') or raw_cart.get('carrito') or []

    try:
        parsed = json.loads(raw_cart)
    except Exception:
        return []

    if isinstance(parsed, dict):
        return parsed.get('cart') or parsed.get('carrito') or []

    return parsed if isinstance(parsed, list) else []


@login_required
def pago_create(request):
    cancel_expired_orders(request.user)
    raw_coupon = (request.GET.get('coupon') or request.POST.get('coupon') or '').strip()
    applied_coupon_code = None
    discount_percent = 0
    coupon_key = raw_coupon.lower()
    if coupon_key in COUPON_DISCOUNTS:
        coupon_code = 'Bookly' + coupon_key[-2:]
        already_used = coupon_was_used(request.user, coupon_code)
        if already_used:
            return render(request, 'core/pago.html', {
                'book': None,
                'show_shipping': True,
                'flow_error': f'El cupón {coupon_code} ya fue utilizado en esta cuenta. Elimínalo para continuar sin descuento.',
            }, status=400)
        applied_coupon_code = coupon_code
        discount_percent = COUPON_DISCOUNTS[coupon_key]

    api_key = settings.FLOW_API_KEY
    secret = settings.FLOW_SECRET
    base_url = settings.FLOW_BASE_URL

    if not (api_key and secret):
        return JsonResponse({'error': 'Flow API key/secret not configured'}, status=500)


    current_origin = request.build_absolute_uri('/')[:-1]
    return_url = f"{current_origin}/flow/return/"
    callback_url = f"{current_origin}/flow/callback/"


    buyer_email = request.user.email
    if not buyer_email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", buyer_email):
        return JsonResponse({'error': 'Email de usuario inválido o faltante. Actualiza tu correo en el perfil.'}, status=400)


    shipping = Address.objects.filter(user=request.user, address_type='shipping', is_default=True).first()


    while True:
        commerce_order = f"ORD-{request.user.id}-{uuid.uuid4().hex[:12]}"
        if not Order.objects.filter(commerce_order=commerce_order).exists():
            break


    cart_items = _parse_cart_payload(request)
    order_items = []
    try:
        for raw_item in cart_items:
            if not isinstance(raw_item, dict):
                continue

            raw_sku = str(raw_item.get('sku') or raw_item.get('id') or '').strip()
            raw_title = str(raw_item.get('title') or raw_item.get('nombre') or raw_item.get('name') or '').strip()

            try:
                quantity = int(raw_item.get('qty') or raw_item.get('quantity') or 1)
            except (TypeError, ValueError):
                quantity = 1
            if quantity < 1:
                quantity = 1

            book = None
            if raw_sku:
                book = Book.objects.filter(sku__iexact=raw_sku, is_active=True).first()
            if book is None and raw_title:
                book = Book.objects.filter(title__iexact=raw_title, is_active=True).first()

            if not book:
                continue

            order_items.append({
                'book': book,
                'quantity': quantity,
            })
    except Exception:
        pass

    if cart_items and not order_items:
        return JsonResponse({'error': 'No se pudieron identificar los libros del carrito.'}, status=400)

    if not order_items:
        return JsonResponse({'error': 'El carrito está vacío.'}, status=400)

    raw_shipping = request.GET.get('shipping') or request.POST.get('shipping')
    try:
        shipping_amount = int(str(raw_shipping)) if raw_shipping is not None else 3990
    except (TypeError, ValueError):
        shipping_amount = 3990
    if shipping_amount not in (3990, 5990):
        shipping_amount = 3990

    subtotal = sum(item['book'].price * item['quantity'] for item in order_items)
    discount_amount = round(subtotal * discount_percent / 100) if applied_coupon_code else 0
    amount = subtotal - discount_amount + shipping_amount

    first_title = None
    if order_items:
        first_title = order_items[0]['book'].title
        if len(order_items) > 1:
            first_title = f"{first_title} y {len(order_items) - 1} más"

    if not first_title:
        try:
            titles_param = request.GET.get('titles') or request.POST.get('titles')
            if titles_param:
                titles_list = json.loads(titles_param)
                if isinstance(titles_list, list) and titles_list:
                    t = str(titles_list[0]).strip()
                    if t and t.lower() != 'producto':
                        first_title = t if len(titles_list) == 1 else f"{t} y {len(titles_list)-1} más"

            if not first_title:
                t_single = request.GET.get('title') or request.POST.get('title')
                if t_single and str(t_single).strip().lower() != 'producto':
                    first_title = str(t_single).strip()
        except Exception:
            pass

    order = Order.objects.create(
        user=request.user,
        commerce_order=commerce_order,
        amount=amount,
        currency='CLP',
        email=buyer_email,
        status='created',
        coupon_code=applied_coupon_code,
        first_item_title=first_title,
        shipping_name=(shipping.name if shipping else None),
        shipping_phone=(shipping.phone if shipping else None),
        shipping_line1=(shipping.line1 if shipping else None),
        shipping_line2=(shipping.line2 if shipping else None),
        shipping_comuna=(shipping.comuna if shipping else None),
        shipping_region=(shipping.region if shipping else None),
        shipping_postal_code=(shipping.postal_code if shipping else None),
    )

    for item_data in order_items:
        OrderItem.objects.create(
            order=order,
            book=item_data['book'],
            quantity=item_data['quantity'],
            price_at_purchase=item_data['book'].price,
        )


    params = {
        'apiKey': api_key,
        'subject': f"Compra: {first_title}" if first_title else 'Compra Bookly',
        'currency': 'CLP',
        'amount': amount,
        'email': buyer_email,
        'paymentMethod': 9,
        'urlReturn': return_url,
        'urlConfirmation': callback_url,
        'commerceOrder': commerce_order,
    }

    s = _flow_sign(params, secret)
    payload = dict(params)
    payload['s'] = s

    try:
        resp = requests.post(f"{base_url}/payment/create", data=payload, timeout=10)
        data = resp.json()
        print('[Flow] create status:', resp.status_code)
        print('[Flow] create response:', data)
    except Exception as e:
        return JsonResponse({'error': 'Flow request failed', 'detail': str(e)}, status=502)

    if resp.status_code != 200 or 'token' not in data:
        order.delete()
        flow_message = data.get('message') if isinstance(data, dict) else None
        friendly_message = flow_message or 'No se pudo crear el pago en Flow. Intenta nuevamente más tarde.'
        return render(request, 'core/pago.html', {
            'book': None,
            'show_shipping': True,
            'flow_error': f"Error al crear pago en Flow: {friendly_message}",
        }, status=400)


    token = data['token']
    order.flow_token = token
    order.flow_order = str(data.get('flowOrder', ''))
    order.save(update_fields=['flow_token', 'flow_order'])

    request.session['last_flow_token'] = token

    provided_url = data.get('url')
    if not provided_url:
        provided_url = 'https://sandbox.flow.cl/app/web/pay.php'
        
    checkout_url = f"{provided_url}?token={token}"
    print('[Flow] Redirecting to NEW order:', checkout_url)
    return redirect(checkout_url)


@csrf_exempt
def flow_return(request):
    token = request.GET.get('token') or request.POST.get('token')
    if not token:
        return redirect('pago')
    print('[Flow] RETURN hit:', request.build_absolute_uri())
    print('[Flow] RETURN method:', request.method)
    print('[Flow] RETURN params GET:', dict(request.GET))
    return redirect(f"/confirmacion_pedido/?token={token}")


def flow_callback(request):
    api_key = settings.FLOW_API_KEY
    secret = settings.FLOW_SECRET
    base_url = settings.FLOW_BASE_URL

    token = request.GET.get('token') or request.POST.get('token')
    if not token:
        return HttpResponse('missing token', status=400)

    print('[Flow] CALLBACK hit:', request.build_absolute_uri())
    print('[Flow] CALLBACK method:', request.method)
    print('[Flow] CALLBACK GET params:', dict(request.GET))
    print('[Flow] CALLBACK POST params:', dict(request.POST))

    params = {'apiKey': api_key, 'token': token}
    s = _flow_sign(params, secret)
    params['s'] = s

    try:
        resp = requests.get(f"{base_url}/payment/getStatus", params=params, timeout=10)
        data = resp.json()
    except Exception:
        return HttpResponse('error', status=502)


    status_map = {1: 'created', 2: 'paid', 3: 'canceled'}
    flow_status = data.get('status')
    mapped = status_map.get(flow_status, 'error')


    try:
        order = Order.objects.get(flow_token=token)
        if order.status != 'paid' or mapped == 'paid':
            order.status = mapped
        order.flow_order = str(data.get('flowOrder', order.flow_order))
        order.save(update_fields=['status', 'flow_order'])


        if order.status == 'paid' and getattr(order, 'coupon_code', None):
            try:
                CouponRedemption.objects.get_or_create(
                    user=order.user,
                    code=order.coupon_code
                )
            except Exception:
                pass
    except Order.DoesNotExist:
        pass

    return HttpResponse('OK')


def flow_debug(request):
    api_key = settings.FLOW_API_KEY
    secret = settings.FLOW_SECRET
    base_url = settings.FLOW_BASE_URL
    site_base = settings.SITE_BASE_URL

    sample_params = {
        'apiKey': api_key or '<missing>',
        'subject': 'Debug Compra Bookly',
        'currency': 'CLP',
        'amount': 1000,
        'email': 'test@example.com',
        'paymentMethod': 9,
        'urlReturn': f"{site_base}/flow/return/",
        'urlConfirmation': f"{site_base}/flow/callback/",
        'commerceOrder': 'DEBUG-ORDER-123',
    }

    canonical = _flow_string_to_sign(sample_params)
    signature = _flow_sign(sample_params, secret) if secret else '<no-secret>'

    return JsonResponse({
        'FLOW_BASE_URL': base_url,
        'SITE_BASE_URL': site_base,
        'FLOW_API_KEY_present': bool(api_key),
        'FLOW_SECRET_present': bool(secret),
        'sample_params': sample_params,
        'canonical_string': canonical,
        'signature': signature,
    })

def destacados(request):
    books_qs = Book.objects.filter(is_active=True)
    discounted = books_qs.filter(discount_percent__gt=0).order_by('-discount_percent', '-created_at')
    if discounted.exists():
        books = discounted
    else:
        books = books_qs.order_by('-created_at')
    paginator = Paginator(books, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'core/destacados.html', {'page_obj': page_obj, 'books': page_obj})


@login_required
def set_default_address(request, address_id: int):
    addr = get_object_or_404(Address, id=address_id, user=request.user, address_type='shipping')
    Address.objects.filter(user=request.user, address_type='shipping', is_default=True).exclude(id=addr.id).update(is_default=False)
    if not addr.is_default:
        addr.is_default = True
        addr.save(update_fields=['is_default'])
    return redirect('checkout')


@login_required
def delete_address(request, address_id: int):
    if request.method != 'POST':
        return redirect('checkout')
    addr = get_object_or_404(Address, id=address_id, user=request.user, address_type='shipping')
    addr.delete()
    return redirect('checkout')

def confirmacion_pedido(request):
    token = request.GET.get('token')
    order = None


    if token:
        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(flow_token=token)
                if not order.confirmation_reached:
                    order.confirmation_reached = True
                if order.status == 'created':
                    order.status = 'paid'
                if not order.stock_updated:
                    for item in order.items.all():
                        book = Book.objects.select_for_update().get(pk=item.book_id)
                        book.stock = max(0, book.stock - item.quantity)
                        book.save(update_fields=['stock', 'updated_at'])
                    order.stock_updated = True
                order.save(update_fields=[
                    'status',
                    'confirmation_reached',
                    'stock_updated',
                    'updated_at',
                ])

            if not request.user.is_authenticated:
                if order.user:
                    login(request, order.user, backend='django.contrib.auth.backends.ModelBackend')
                    print(f"[Auto-Login] Sesión recuperada exitosamente para: {order.user.username}")
        except Order.DoesNotExist:
            order = None

    if not request.user.is_authenticated and not order:
        return redirect('index')

    if order and getattr(order, 'coupon_code', None) and order.user:
        try:
            CouponRedemption.objects.get_or_create(
                user=order.user,
                code=order.coupon_code
            )
        except Exception:
            pass

    buyer_name = None
    order_items_summary = []
    if order:
        try:
            full_name = (order.user.get_full_name() or '').strip()
        except Exception:
            full_name = ''
        buyer_name = getattr(order, 'shipping_name', None) or full_name or getattr(order.user, 'username', None)
        order_items_summary = [
            {
                'title': item.book.title,
                'quantity': item.quantity,
                'unit_price': item.price_at_purchase,
                'line_total': item.quantity * item.price_at_purchase,
            }
            for item in order.items.select_related('book').all()
        ]

    context = {
        'order': order,
        'buyer_name': buyer_name,
        'order_items_summary': order_items_summary,
        'status': getattr(order, 'status', None),
        'amount': getattr(order, 'amount', None),
        'currency': getattr(order, 'currency', None),
        'commerce_order': getattr(order, 'commerce_order', None),
        'flow_order': getattr(order, 'flow_order', None),
        'shipping_name': getattr(order, 'shipping_name', None),
        'shipping_phone': getattr(order, 'shipping_phone', None),
        'shipping_line1': getattr(order, 'shipping_line1', None),
        'shipping_line2': getattr(order, 'shipping_line2', None),
        'shipping_comuna': getattr(order, 'shipping_comuna', None),
        'shipping_region': getattr(order, 'shipping_region', None),
        'shipping_postal_code': getattr(order, 'shipping_postal_code', None),
    }
    return render(request, 'core/confirmacion_pedido.html', context)

def search(request):
    query = request.GET.get('q', '').strip()
    selected_category = request.GET.get('category', '').strip()
    results = Book.objects.filter(is_active=True)
    
    if query:
        results = results.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(category__icontains=query)
        )
    if selected_category:
        results = results.filter(category__iexact=selected_category)
    results = results.order_by('-created_at') if query or selected_category else Book.objects.none()
    
    context = {
        'query': query,
        'selected_category': selected_category,
        'results': results,
        'count': results.count() if results else 0,
    }
    return render(request, 'core/search.html', context)


def mis_pedidos(request):
    cancel_expired_orders(request.user)
    # 1. Obtener la lista completa
    order_list = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # 2. Configurar el paginador (10 items por página)
    paginator = Paginator(order_list, 10)
    
    # 3. Capturar el número de página actual desde la URL (ej: ?page=2)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    
    # 4. Enviar el objeto paginado a la plantilla
    return render(request, 'core/mis_pedidos.html', { 'orders': orders })


@login_required
def mi_perfil(request):
    user = request.user

    if request.method == 'POST':
        # 1. Obtener los datos del formulario
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        rut = request.POST.get('rut', '').strip()
        doc_type = request.POST.get('doc_type', 'RUT').strip()

        # 2. Guardar los datos en el modelo User nativo
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if email:
            user.email = email
        user.save()

        # 3. Guardar los datos extendidos en Profile (creándolo si hace falta)
        try:
            perfil = user.profile
        except ObjectDoesNotExist:
            perfil = Profile.objects.create(user=user)

        perfil.rut = rut
        perfil.phone = phone
        perfil.doc_type = doc_type
        perfil.save()

        # Redirige a la misma página para recargar los datos actualizados
        return redirect('mi_perfil')

    return render(request, 'core/mi_perfil.html')




@login_required
def mi_contrasena(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        
        # Capturamos la nueva contraseña del formulario para validarla
        new_password = request.POST.get('new_password1', '')

        # Validaciones personalizadas idénticas al registro
        if (
            len(new_password) < 8 or
            not re.search(r"[A-Z]", new_password) or
            not re.search(r"[\W\_]", new_password)
        ):
            messages.error(request, 'La nueva contraseña debe tener mínimo 8 caracteres, una mayúscula y un símbolo.')
        elif form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            send_password_changed_email(user)
            messages.success(request, 'Tu contraseña ha sido actualizada correctamente.')
            return redirect('mi_contrasena')
        else:
            messages.error(request, 'Por favor, corrige los errores indicados abajo.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'core/mi_contrasena.html', {'form': form})
