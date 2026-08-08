from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.db import IntegrityError
from django.utils import timezone
from django.db.models import Q
import re
import hmac
import hashlib
import requests
import time
import uuid
import json

from .models import Order, OrderItem, Address, Book, CouponRedemption

# Create your views here.

def index(request):
    books = Book.objects.order_by('-created_at')
    return render(request, 'core/index.html', { 'books': books })

def libro_detalles(request, sku: str):
    book = get_object_or_404(Book, sku=sku)
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


def logout_view(request):
    logout(request)
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


            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if email:
                user.email = email
            user.save()


            if rut:
                request.session['checkout_rut'] = rut


            if phone:
                default_addr = Address.objects.filter(user=user, address_type='shipping', is_default=True).first()
                if default_addr:
                    default_addr.phone = phone
                    default_addr.save(update_fields=['phone'])

            return redirect('checkout')


    coupon_already_used = (
        CouponRedemption.objects.filter(user=user, code__iexact='Bookly10').exists() or
        Order.objects.filter(user=user, coupon_code__iexact='Bookly10').exists()
    )


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
    user_phone = (default_address.phone if default_address else '')


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
        'user_rut': request.session.get('checkout_rut', ''),
        'default_street': default_street,
        'default_number': default_number,
        'show_shipping': False,
        'has_user_data': has_user_data,
        'can_continue': has_user_data and has_addresses,
        'coupon_already_used': coupon_already_used,
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

    coupon_already_used = (
        CouponRedemption.objects.filter(user=request.user, code__iexact='Bookly10').exists() or
        Order.objects.filter(user=request.user, coupon_code__iexact='Bookly10').exists()
    )

    sku = request.GET.get('sku')
    book = None
    if sku:
        try:
            book = Book.objects.get(sku=sku)
        except Book.DoesNotExist:
            book = None
    context = {
        'book': book,
        'show_shipping': True,
        'coupon_already_used': coupon_already_used,
    }
    return render(request, 'core/entrega.html', context)


@login_required
def pago(request):
    sku = request.GET.get('sku')
    book = None
    if sku:
        try:
            book = Book.objects.get(sku=sku)
        except Book.DoesNotExist:
            book = None

    coupon_already_used = (
        CouponRedemption.objects.filter(user=request.user, code__iexact='Bookly10').exists() or
        Order.objects.filter(user=request.user, coupon_code__iexact='Bookly10').exists()
    )

    return render(request, 'core/pago.html', {
        'book': book,
        'show_shipping': True,
        'coupon_already_used': coupon_already_used,
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

    raw_amount = request.GET.get('amount') or request.POST.get('amount')
    try:
        amount = int(str(raw_amount)) if raw_amount is not None else 1000
    except (TypeError, ValueError):
        amount = 1000
    if amount <= 0:
        amount = 1000

    raw_coupon = (request.GET.get('coupon') or request.POST.get('coupon') or '').strip()
    applied_coupon_code = None
    if raw_coupon and raw_coupon.lower() == 'bookly10':
        already_used = (
            CouponRedemption.objects.filter(user=request.user, code__iexact='Bookly10').exists()
            or Order.objects.filter(user=request.user, coupon_code__iexact='Bookly10').exists()
        )
        if already_used:
            return render(request, 'core/pago.html', {
                'book': None,
                'show_shipping': True,
                'flow_error': 'El cupón Bookly10 ya fue utilizado en esta cuenta. Elimínalo para continuar sin descuento.',
            }, status=400)
        applied_coupon_code = 'Bookly10'

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
                book = Book.objects.filter(sku__iexact=raw_sku).first()
            if book is None and raw_title:
                book = Book.objects.filter(title__iexact=raw_title).first()

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
        order.status = mapped
        order.flow_order = str(data.get('flowOrder', order.flow_order))
        order.save(update_fields=['status', 'flow_order'])


        if mapped == 'paid' and getattr(order, 'coupon_code', None):
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
    books_qs = Book.objects.all()
    discounted = books_qs.filter(discount_percent__gt=0).order_by('-discount_percent', '-created_at')
    if discounted.exists():
        books = discounted[:12]
    else:
        books = books_qs.order_by('-created_at')[:12]
    return render(request, 'core/destacados.html', { 'books': books })


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
            order = Order.objects.get(flow_token=token)

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
    results = []
    
    if query:
        results = Book.objects.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(category__icontains=query)
        ).order_by('-created_at')
    
    context = {
        'query': query,
        'results': results,
        'count': results.count() if results else 0,
    }
    return render(request, 'core/search.html', context)





