const flowActions = document.querySelector('.flow-actions');
const defaultFlowActionsDisplay = flowActions ? getComputedStyle(flowActions).display : 'flex';

function toggleFlowActions(show) {
    if (!flowActions) {
        return;
    }
    flowActions.style.display = show ? defaultFlowActionsDisplay : 'none';
}

function initDireccionesPanel() {
    const panel = document.getElementById('listaDirecciones');
    const toggleBtn = document.querySelector('.btn-direcciones');

    if (!panel || !toggleBtn) {
        return;
    }

    toggleBtn.addEventListener('click', function () {
        const isVisible = panel.classList.toggle('is-visible');
        panel.hidden = !isVisible;
        this.textContent = isVisible ? 'Ocultar direcciones' : 'Mis direcciones';
        this.setAttribute('aria-expanded', isVisible);
    });

    panel.addEventListener('click', function (event) {
        const selectBtn = event.target.closest('.btn-usar-direccion');
        if (!selectBtn) {
            return;
        }

        panel.querySelectorAll('.direccion-item').forEach((card) => card.classList.remove('direccion-item-activa'));
        const item = selectBtn.closest('.direccion-item');
        if (item) {
            item.classList.add('direccion-item-activa');
        }
    });
}

// Funciones para editar DATOS PERSONALES
function editarDatos() {
    document.getElementById('datosResumen').style.display = 'none';
    document.getElementById('datosFormulario').style.display = 'block';
    document.getElementById('separador1').style.display = 'none';
    document.getElementById('direccionResumen').style.display = 'none';
    toggleFlowActions(false);
}

function cancelarEdicionDatos() {
    document.getElementById('datosFormulario').style.display = 'none';
    document.getElementById('datosResumen').style.display = 'block';
    document.getElementById('separador1').style.display = 'block';
    document.getElementById('direccionResumen').style.display = 'block';
    toggleFlowActions(true);
}

function guardarDatos() {
    alert('Datos personales guardados correctamente');
    cancelarEdicionDatos();
}

// Funciones para editar DIRECCIÓN
function editarDireccion() {
    document.getElementById('direccionResumen').style.display = 'none';
    document.getElementById('direccionFormulario').style.display = 'block';
    document.getElementById('datosResumen').style.display = 'none';
    document.getElementById('separador1').style.display = 'none';
    toggleFlowActions(false);
}

function cancelarEdicionDireccion() {
    document.getElementById('direccionFormulario').style.display = 'none';
    document.getElementById('direccionResumen').style.display = 'block';
    document.getElementById('datosResumen').style.display = 'block';
    document.getElementById('separador1').style.display = 'block';
    toggleFlowActions(true);
}

function guardarDireccion() {
    alert('Dirección guardada correctamente');
    cancelarEdicionDireccion();
}

initDireccionesPanel();

// Mostrar / ocultar ítem de producto en resumen
(function () {
    var vmBtn = document.querySelector('.ver-menos');
    if (!vmBtn) return;
    vmBtn.addEventListener('click', function () {
        const productItem = document.querySelector('.product-item');
        if (!productItem) return;
        if (productItem.style.display === 'none') {
            productItem.style.display = 'flex';
            this.textContent = 'VER MENOS ∧';
        } else {
            productItem.style.display = 'none';
            this.textContent = 'VER MÁS ∨';
        }
    });
})();

// Eliminar y aplicar cupón en checkout y pago
(function () {
    var couponBox = document.querySelector('.coupon-applied');
    var couponTextSpan = couponBox ? couponBox.firstChild : null;
    var couponClose = couponBox ? couponBox.querySelector('.coupon-remove') : null;
    var applyBtn = document.querySelector('.btn-apply');
    var input = document.querySelector('.coupon-input input');

    function getActiveCoupon() {
        try {
            return JSON.parse(localStorage.getItem('booklyCoupon') || 'null');
        } catch (e) {
            return null;
        }
    }

    function setActiveCoupon(c) {
        if (!c) {
            localStorage.removeItem('booklyCoupon');
        } else {
            localStorage.setItem('booklyCoupon', JSON.stringify(c));
        }
    }

    function refreshCouponUI() {
        var c = getActiveCoupon();
        if (!couponBox) return;
        if (c) {
            couponBox.style.display = 'flex';
            if (couponTextSpan && couponTextSpan.nodeType === Node.TEXT_NODE) {
                couponTextSpan.textContent = c.code;
            } else {
                couponBox.childNodes[0].nodeValue = c.code + ' ';
            }
        } else {
            couponBox.style.display = 'none';
        }
    }

    function applyCoupon() {
        if (!input) return;
        var code = (input.value || '').trim();
        if (!code) {
            alert('Ingresa un código de cupón.');
            return;
        }
        if (code.toLowerCase() !== 'bookly10') {
            alert('Cupón inválido. Usa "Bookly10".');
            return;
        }
        if (typeof window !== 'undefined' && window.couponAlreadyUsed === 'true') {
            alert('El cupón Bookly10 ya fue utilizado en una compra anterior de esta cuenta. No puedes volver a usarlo.');
            try {
                setActiveCoupon(null);
                refreshCouponUI();
                input.value = '';
                if (typeof renderSummary === 'function') renderSummary();
            } catch (e) {}
            return;
        }
        setActiveCoupon({ code: 'Bookly10', type: 'percent_one_per_item', value: 10 });
        refreshCouponUI();
        input.value = '';
        try { if (typeof renderSummary === 'function') renderSummary(); } catch (e) {}
        alert('Cupón Bookly10 aplicado: 10% en 1 unidad de cada producto.');
    }


    if (couponBox) refreshCouponUI();

    if (couponClose) {
        couponClose.addEventListener('click', function () {
            setActiveCoupon(null);
            refreshCouponUI();
            try { if (typeof renderSummary === 'function') renderSummary(); } catch (e) {}
        });
    }

    if (applyBtn) {
        applyBtn.addEventListener('click', function () {
            applyCoupon();
        });
    }
})();


// Calendario para envío planificado
function toggleDatePicker(event) {
    event.preventDefault();
    const datePicker = document.getElementById('deliveryDateTime');
    const link = event.target;

    if (datePicker.style.display === 'none') {
        datePicker.style.display = 'block';
        link.textContent = 'Ocultar calendario';

        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        tomorrow.setHours(10, 0, 0, 0);

        const minDate = tomorrow.toISOString().slice(0, 16);
        datePicker.min = minDate;

        document.querySelector('input[value="planificado"]').checked = true;
    } else {
        datePicker.style.display = 'none';
        link.textContent = 'Elige día y hora';
    }
}


document.addEventListener('DOMContentLoaded', function () {
    const shippingOptions = document.querySelectorAll('.shipping-option');
    const radios = document.querySelectorAll('input[name="envio"]');

    function updateActiveState() {
        const selectedRadio = document.querySelector('input[name="envio"]:checked');
        if (!selectedRadio) return;

        const selectedValue = selectedRadio.value;

        shippingOptions.forEach(option => {
            const radio = option.querySelector('input[name="envio"]');
            if (radio && radio.value === selectedValue) {
                option.classList.add('active');
            } else {
                option.classList.remove('active');
            }
        });

        updateShippingFromSelection();
    }

    radios.forEach(radio => {
        radio.addEventListener('change', updateActiveState);
    });

    if (shippingOptions.length > 0 && radios.length > 0) {
        updateShippingFromSelection();
    }

    const planificadoLink = document.querySelector('.shipping-link');
    if (planificadoLink) {
        planificadoLink.addEventListener('click', function () {
            setTimeout(updateActiveState, 0);
        });
    }

    if (radios.length > 0) {
        updateActiveState();
    }

    const goPayLink = document.getElementById('linkIrPagar');
    if (goPayLink) {
        goPayLink.addEventListener('click', function (ev) {
            const selected = document.querySelector('input[name="envio"]:checked');
            if (!selected) {
                ev.preventDefault();
                alert('Selecciona un método de envío para continuar.');
                return;
            }
            if (selected.value === 'planificado') {
                const dp = document.getElementById('deliveryDateTime');
                if (!dp || !dp.value) {
                    ev.preventDefault();
                    alert('Elige día y hora para el envío planificado antes de continuar.');
                    return;
                }
            }
        });
    }
});



// Rellenar entrega con el primer producto del carrito (localStorage)
document.addEventListener('DOMContentLoaded', function () {
    var container = document.getElementById('deliveryProduct');
    if (!container) return;
    var hasServerBook = !!document.querySelector('.delivery-product-sku');
    if (hasServerBook) return;

    try {
        var raw = localStorage.getItem('booklyCart');
        if (!raw || raw === '[]') {
            raw = localStorage.getItem('bookly_cart') || '[]';
        }
        var cart = JSON.parse(raw || '[]');
        if (Array.isArray(cart) && cart.length > 0) {
            var item = cart[0];
            var imgEl = container.querySelector('.delivery-product-img');
            var nameEl = container.querySelector('#deliveryName');
            var qtyEl = container.querySelector('#deliveryQty');
            if (imgEl && item.image) imgEl.src = item.image;
            if (imgEl && item.title) imgEl.alt = item.title;
            if (nameEl && item.title) nameEl.textContent = item.title;
            if (qtyEl) qtyEl.textContent = 'Cantidad: ' + (item.qty || 1);
            var info = container.querySelector('.delivery-product-info');
            if (info) {
                if (item.author) {
                    var p = document.createElement('p');
                    p.className = 'delivery-product-brand';
                    p.textContent = item.author;
                    info.prepend(p);
                }
                if (item.sku) {
                    var psku = document.createElement('p');
                    psku.className = 'delivery-product-sku';
                    psku.textContent = 'SKU: ' + item.sku;
                    info.appendChild(psku);
                }
            }
        }
    } catch (e) {
    }
});


(function () {
    function fmt(n) { try { return new Intl.NumberFormat('es-CL').format(n || 0); } catch (e) { return (n || 0).toString(); } }

    function getActiveCoupon() {
        try { return JSON.parse(localStorage.getItem('booklyCoupon') || 'null'); } catch (e) { return null; }
    }

    function renderSummary() {
        var list = document.getElementById('summaryList');
        var subEl = document.getElementById('sumSubtotalBase2');
        var totEl = document.getElementById('sumTotalBase2');
        if (!list || !subEl || !totEl) return;
        var items = [];
        try {
            var raw = localStorage.getItem('booklyCart');
            if (!raw || raw === '[]') {
                raw = localStorage.getItem('bookly_cart') || '[]';
            }
            items = JSON.parse(raw || '[]');
        } catch (e) {
            items = [];
        }
        list.innerHTML = '';
        if (!items.length) {
            list.innerHTML = '<p style="color:#666;">Tu carrito está vacío.</p>';
            subEl.textContent = '$0';
            var ivaElEmpty = document.getElementById('sumIvaBase2');
            if (ivaElEmpty) ivaElEmpty.textContent = '$0';
            var discElEmpty = document.getElementById('sumDiscountBase2');
            if (discElEmpty) discElEmpty.textContent = '$0';
            totEl.textContent = '$2.990';
            return;
        }
        var gross = 0;
        items.forEach(function (it) {
            var qty = parseInt(it.qty || 1, 10) || 1; var price = parseInt(it.price || 0, 10) || 0; var line = qty * price; gross += line; var row = document.createElement('div'); row.className = 'product-item'; row.innerHTML = '<div class="product-image">\n'
                + '<img src="' + (it.image || 'https://via.placeholder.com/60x60') + '" alt="' + (it.title || 'Producto') + '" loading="lazy">\n'
                + '</div>\n'
                + '<div class="product-details">\n'
                + '<div class="product-brand">&nbsp;</div>\n'
                + '<div class="product-name">' + (it.title || 'Producto') + '</div>\n'
                + '<div class="product-size">&nbsp;</div>\n'
                + '<div class="product-quantity">Cantidad: ' + qty + ' u.</div>\n'
                + '<div class="delivery-badge">\n'
                + '<span class="icon icon-truck" aria-hidden="true">\n'
                + '<svg viewBox="0 0 24 24" focusable="false">\n'
                + '<path d="M3 7h11v7H3z" fill="currentColor" />\n'
                + '<path d="M14 9h3l3 4v4h-2" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" />\n'
                + '<circle cx="7.5" cy="18.5" r="2" fill="currentColor" />\n'
                + '<circle cx="18.5" cy="18.5" r="2" fill="currentColor" />\n'
                + '</svg>\n'
                + '</span> Envío a domicilio\n'
                + '</div>\n'
                + '</div>\n'
                + '<div class="product-price-row">\n'
                + '<span class="product-price-label">Total sin envío:</span>\n'
                + '<span class="product-price">$' + fmt(line) + '</span>\n'
                + '</div>';
            list.appendChild(row);
        });


        var coupon = getActiveCoupon();
        var discount = 0;
        if (coupon && coupon.code === 'Bookly10') {
            items.forEach(function (it) {
                var price = parseInt(it.price || 0, 10) || 0;
                discount += Math.round(price * 0.10);
            });
        }
        var grossAfter = Math.max(0, gross - discount);

        var ivaRate = 0.19;
        var netSubtotal = Math.max(0, Math.round(gross * (1 - ivaRate)));
        var ivaAmount = Math.max(0, Math.round(gross * ivaRate));
        subEl.textContent = '$' + fmt(netSubtotal);
        var ivaEl = document.getElementById('sumIvaBase2');
        if (ivaEl) ivaEl.textContent = '$' + fmt(ivaAmount);
        var discEl = document.getElementById('sumDiscountBase2');
        if (discEl) {
            discEl.textContent = (discount > 0 ? '-$' + fmt(discount) : '$0');
        }

        var totalsBox = document.getElementById('summaryTotals');
        var envio = 0;
        if (totalsBox) {
            var shipEl = document.getElementById('sumShippingBase2');
            var hasShippingOptions = !!document.querySelector('input[name="envio"]');

            console.log('DEBUG - hasShippingOptions:', hasShippingOptions, 'shipEl:', shipEl);

            if (!hasShippingOptions && shipEl) {
                var saved = parseInt(localStorage.getItem('booklyShipping') || '0', 10) || 0;
                console.log('Restaurando envío desde localStorage:', saved);
                if (saved > 0) {
                    totalsBox.setAttribute('data-shipping', String(saved));
                    shipEl.textContent = '$' + fmt(saved);
                    envio = saved;
                } else {
                    console.log('Saved shipping es 0 o inválido');
                }
            } else {
                console.log('Usando data-shipping del HTML');
                var ds = parseInt(totalsBox.getAttribute('data-shipping') || '0', 10);
                envio = isNaN(ds) ? 0 : ds;
            }
        }
        var total = grossAfter + envio;
        totEl.textContent = '$' + fmt(total);
        console.log('Total calculado:', total, '(gross:', gross, '+ envío:', envio, ')');

        var installmentsEl = document.getElementById('installmentsText');
        if (installmentsEl && total > 0) {
            var installmentAmount = Math.round(total / 6);
            installmentsEl.textContent = 'hasta en 6 x $' + fmt(installmentAmount) + ' sin interés*';
        }
    }

    window.renderSummary = renderSummary;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', renderSummary);
    } else {
        renderSummary();
    }
})();

// actualiza el resumen
function updateShippingFromSelection() {
    try {
        var totalsBox = document.getElementById('summaryTotals');
        if (!totalsBox) return;
        var selected = document.querySelector('.shipping-option.active .shipping-price');
        var amount = 0;
        if (selected && selected.textContent) {
            var raw = String(selected.textContent).replace(/[^0-9]/g, '');
            amount = parseInt(raw || '0', 10) || 0;
        }
        console.log('Guardando envío seleccionado:', amount);
        try {
            localStorage.setItem('booklyShipping', String(amount));
        } catch (e) {
            console.error('Error guardando en localStorage:', e);
        }
        totalsBox.setAttribute('data-shipping', String(amount));
        var shipEl = document.getElementById('sumShippingBase2');
        if (shipEl) {
            shipEl.textContent = '$' + new Intl.NumberFormat('es-CL').format(amount);
        }
        try {
            if (typeof renderSummary === 'function') {
                renderSummary();
            }
        } catch (e) { /* no-op */ }
    } catch (e) {
        console.error('Error en updateShippingFromSelection:', e);
    }
}


document.addEventListener('DOMContentLoaded', function () {
    try {
        var totalsBox = document.getElementById('summaryTotals');
        if (!totalsBox) return;
        var hasShippingOptions = !!document.querySelector('.shipping-option');
        if (hasShippingOptions) return;
        var shipEl = document.getElementById('sumShippingBase2');
        if (!shipEl) return;
        var saved = parseInt(localStorage.getItem('booklyShipping') || '0', 10) || 0;
        console.log('Restaurando envío desde localStorage:', saved);
        if (saved > 0) {
            totalsBox.setAttribute('data-shipping', String(saved));
            shipEl.textContent = '$' + new Intl.NumberFormat('es-CL').format(saved);
            var totEl = document.getElementById('sumTotalBase2');
            var subEl = document.getElementById('sumSubtotalBase2');
            var ivaEl = document.getElementById('sumIvaBase2');
            if (!totEl || !subEl || !ivaEl) return;
            var net = parseInt(String(subEl.textContent).replace(/[^0-9]/g, ''), 10) || 0;
            var iva = parseInt(String(ivaEl.textContent).replace(/[^0-9]/g, ''), 10) || 0;
            var gross = net + iva;
            totEl.textContent = '$' + new Intl.NumberFormat('es-CL').format(gross + saved);
            console.log('Total actualizado con envío:', gross + saved);
        }
    } catch (e) {
        console.error('Error restaurando envío:', e);
    }
});

// Enviar el total a Flow al presionar Pagar
document.addEventListener('DOMContentLoaded', function () {
    try {
        var pagarLink = document.getElementById('linkPagarFlow') || document.querySelector('.flow-actions a[href*="pago_create"]');
        var pagarBtn = document.getElementById('btnPagarFlow');
        if (!pagarLink) return;
        function handlePay(ev) {
            ev.preventDefault();
            try {
                if (pagarBtn) { pagarBtn.disabled = true; pagarBtn.style.pointerEvents = 'none'; }
                if (pagarLink) { pagarLink.style.pointerEvents = 'none'; }
            } catch (e) { }
            var totalEl = document.getElementById('sumTotalBase2');
            var total = 0;
            if (totalEl && totalEl.textContent) {
                total = parseInt(String(totalEl.textContent).replace(/[^0-9]/g, ''), 10) || 0;
            }

            if (total <= 0) {
                try {
                    var raw = localStorage.getItem('booklyCart');
                    if (!raw || raw === '[]') raw = localStorage.getItem('bookly_cart') || '[]';
                    var items = JSON.parse(raw || '[]');
                    var gross = 0;
                    items.forEach(function (it) { var q = parseInt(it.qty || 1, 10) || 1; var p = parseInt(it.price || 0, 10) || 0; gross += q * p; });
                    var ship = parseInt(localStorage.getItem('booklyShipping') || '0', 10) || 0;
                    total = gross + ship;
                } catch (e) { }
            }
            if (!total || total <= 0) {
                alert('No se pudo determinar el total a cobrar.');
                return;
            }
            var url = new URL(pagarLink.href, window.location.origin);
            url.searchParams.set('amount', String(total));
            try {
                var activeCoupon = null;
                try { activeCoupon = JSON.parse(localStorage.getItem('booklyCoupon') || 'null'); } catch (_) { activeCoupon = null; }
                if (activeCoupon && activeCoupon.code && activeCoupon.code.toLowerCase() === 'bookly10') {
                    url.searchParams.set('coupon', activeCoupon.code);
                }
            } catch (e) { }

            try {
                var rawCart = localStorage.getItem('booklyCart') || localStorage.getItem('bookly_cart') || '[]';
                var arr = [];
                try { arr = JSON.parse(rawCart || '[]'); } catch (_) { arr = []; }
                var titles = [];
                if (Array.isArray(arr)) {
                    arr.forEach(function (it) {
                        var t = (it && (it.title || it.nombre || it.name)) ? String(it.title || it.nombre || it.name).trim() : '';
                        if (t && t.toLowerCase() !== 'producto') { titles.push(t); }
                    });
                }
                if (titles.length > 0) {
                    url.searchParams.set('titles', JSON.stringify(titles));
                } else {
                    var firstTitle = '';
                    var nameEl = document.querySelector('.delivery-product-name');
                    if (nameEl && nameEl.textContent) { firstTitle = nameEl.textContent.trim(); }
                    if (firstTitle && firstTitle.toLowerCase() !== 'producto') {
                        url.searchParams.set('title', firstTitle);
                    }
                }
            } catch (e) { }
            window.location.href = url.toString();
        }
        if (pagarBtn) {
            pagarBtn.addEventListener('click', handlePay);
        } else {
            pagarLink.addEventListener('click', handlePay);
        }
    } catch (e) { /* no-op */ }
});