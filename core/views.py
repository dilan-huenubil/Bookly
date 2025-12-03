from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
import re
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db import IntegrityError
import hmac
import hashlib
import requests
from urllib.parse import urlencode
import time
import uuid
from .models import Order, Address, Book

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

    # -------------------------------
    # REGISTRO
    # -------------------------------
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

    # -------------------------------
    # LOGIN (seguro + next)
    # -------------------------------
    elif form_type == "login":
        identifier = request.POST.get('username')
        password = request.POST.get('password')

        # Capturar next desde POST o GET
        next_url = request.POST.get('next') or request.GET.get('next')

        user = authenticate(request, username=identifier, password=password)

        if user is None:
            return render(request, 'core/register-login.html', {
                'login_error': 'Usuario o contraseña incorrectos',
                'register_error': ''
            })

        login(request, user)

        # =============================
        # VALIDAR QUE NEXT SEA INTERNO
        # =============================
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()}
        ):
            return redirect(next_url)

        # Si no hay next o es inválido → ir al index
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
    # Handle create/update address submissions
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
            ciudad = (request.POST.get('ciudad') or '').strip()
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
            addr.ciudad = ciudad or addr.ciudad or ''
            addr.postal_code = postal_code or addr.postal_code or ''
            addr.save()

            if make_default:
                Address.objects.filter(user=user, address_type='shipping', is_default=True).exclude(id=addr.id).update(is_default=False)
                addr.is_default = True
                addr.save(update_fields=['is_default'])

            return redirect('checkout')

    # Load user info and shipping addresses from DB (GET or after POST redirect)
    addresses = Address.objects.filter(user=user, address_type='shipping').order_by('-is_default', '-updated_at')
    default_address = addresses.filter(is_default=True).first() or addresses.first()

    context = {
        'user': user,
        'addresses': addresses,
        'default_address': default_address,
        'has_addresses': addresses.exists(),
        'user_phone': (default_address.phone if default_address else ''),
        'show_shipping': False,
    }
    return render(request, 'core/checkout.html', context)

@login_required
def entrega(request):
    # Intentar cargar un libro desde la BD si se proporciona SKU
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
    }
    return render(request, 'core/entrega.html', context)


@login_required
def pago(request):
    # Cargar libro desde BD opcional por SKU
    sku = request.GET.get('sku')
    book = None
    if sku:
        try:
            book = Book.objects.get(sku=sku)
        except Book.DoesNotExist:
            book = None
    return render(request, 'core/pago.html', { 'book': book, 'show_shipping': True })

# =============================
# Flow payment integration (sandbox)
# =============================

def _flow_string_to_sign(params: dict) -> str:
    # Flow expects a canonical string: key=value joined by '&', sorted by key, no URL encoding
    items = sorted((k, str(v)) for k, v in params.items() if k != 's')
    return '&'.join(f"{k}={v}" for k, v in items)

def _flow_sign(params: dict, secret: str) -> str:
    data = _flow_string_to_sign(params)
    return hmac.new(secret.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()


@login_required
def pago_create(request):
    # Amount comes from client-side computed total (subtotal+IVA+envío)
    raw_amount = request.GET.get('amount') or request.POST.get('amount')
    try:
        amount = int(str(raw_amount)) if raw_amount is not None else 1000
    except (TypeError, ValueError):
        amount = 1000
    # Safety floor
    if amount <= 0:
        amount = 1000
    api_key = settings.FLOW_API_KEY
    secret = settings.FLOW_SECRET
    base_url = settings.FLOW_BASE_URL

    if not (api_key and secret):
        return JsonResponse({'error': 'Flow API key/secret not configured'}, status=500)

    return_url = f"{settings.SITE_BASE_URL}/flow/return/"
    callback_url = f"{settings.SITE_BASE_URL}/flow/callback/"
    # Generate a unique commerce order id (Flow requires unique value)
    def _new_commerce_order():
        return f"ORD-{request.user.id}-{uuid.uuid4().hex[:12]}"
    commerce_order = _new_commerce_order()

    # Validate buyer email: Flow requires a valid email
    buyer_email = request.user.email
    if not buyer_email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", buyer_email):
        return JsonResponse({'error': 'Email de usuario inválido o faltante. Actualiza tu correo en el perfil.'}, status=400)

    # Try to use user's default shipping address snapshot
    shipping = Address.objects.filter(user=request.user, address_type='shipping', is_default=True).first()

    # Create local order with snapshot if available (retry on rare UUID collision)
    for _ in range(3):
        try:
            order = Order.objects.create(
                user=request.user,
                commerce_order=commerce_order,
                amount=amount,
                currency='CLP',
                email=buyer_email,
                status='created',
                shipping_name=(shipping.name if shipping else None),
                shipping_phone=(shipping.phone if shipping else None),
                shipping_line1=(shipping.line1 if shipping else None),
                shipping_line2=(shipping.line2 if shipping else None),
                shipping_comuna=(shipping.comuna if shipping else None),
                shipping_ciudad=(shipping.ciudad if shipping else None),
                shipping_region=(shipping.region if shipping else None),
                shipping_postal_code=(shipping.postal_code if shipping else None),
            )
            break
        except IntegrityError:
            commerce_order = _new_commerce_order()
    else:
        return JsonResponse({'error': 'No se pudo generar una orden única. Intenta nuevamente.'}, status=500)

    params = {
        'apiKey': api_key,
        'subject': 'Compra Bookly',
        'currency': 'CLP',
        'amount': amount,
        'email': buyer_email,
        'paymentMethod': 9,  # Webpay Plus
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
        return JsonResponse({'error': 'Flow error', 'response': data}, status=500)

    # Persist Flow response
    token = data['token']
    order.flow_token = token
    order.flow_order = str(data.get('flowOrder', ''))
    order.save(update_fields=['flow_token', 'flow_order'])
    # Prefer Flow-provided URL for redirection
    provided_url = data.get('url', 'https://sandbox.flow.cl/flow/redirect')
    checkout_url = f"{provided_url}?token={token}"
    print('[Flow] Redirecting to:', checkout_url)
    return redirect(checkout_url)


@login_required
def flow_return(request):
    # User returns from Flow; token present in query
    token = request.GET.get('token')
    if not token:
        return redirect('pago')
    # Log incoming return for diagnostics
    print('[Flow] RETURN hit:', request.build_absolute_uri())
    print('[Flow] RETURN params:', dict(request.GET))
    # Optionally fetch payment status here
    return render(request, 'core/pago.html', {'flow_token': token, 'message': 'Retorno desde Flow'})


def flow_callback(request):
    # Server-to-server confirmation
    api_key = settings.FLOW_API_KEY
    secret = settings.FLOW_SECRET
    base_url = settings.FLOW_BASE_URL

    token = request.GET.get('token') or request.POST.get('token')
    if not token:
        return HttpResponse('missing token', status=400)
    # Log incoming callback for diagnostics
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

    # Update local order status based on Flow status
    # Status mapping: 1=created, 2=paid, 3=canceled
    status_map = {1: 'created', 2: 'paid', 3: 'canceled'}
    flow_status = data.get('status')
    mapped = status_map.get(flow_status, 'error')

    # Find order by token
    try:
        order = Order.objects.get(flow_token=token)
        order.status = mapped
        order.flow_order = str(data.get('flowOrder', order.flow_order))
        order.save(update_fields=['status', 'flow_order'])
    except Order.DoesNotExist:
        pass

    return HttpResponse('OK')


def flow_debug(request):
    # Diagnostics endpoint to verify loaded settings and signature behavior
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
    # Libros destacados: priorizar con descuento, luego recientes
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
    # Allow only POST for deletion to avoid accidental deletes via link clicks
    if request.method != 'POST':
        return redirect('checkout')
    addr = get_object_or_404(Address, id=address_id, user=request.user, address_type='shipping')
    addr.delete()
    return redirect('checkout')

@login_required
def confirmacion_pedido(request):
    return render(request, 'core/confirmacion_pedido.html')
