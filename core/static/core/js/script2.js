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

// Toggle ver menos/ver más (protegido si no existe el botón)
(function(){
    var vmBtn = document.querySelector('.ver-menos');
    if(!vmBtn) return;
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

// Eliminar cupón (protegido si no existe)
(function(){
    var couponClose = document.querySelector('.coupon-applied .coupon-remove');
    if(!couponClose) return;
    couponClose.addEventListener('click', function () {
        var parent = this.parentElement;
        if (parent) parent.style.display = 'none';
    });
})();

// Aplicar cupón (protegido si no existe)
(function(){
    var applyBtn = document.querySelector('.btn-apply');
    if(!applyBtn) return;
    applyBtn.addEventListener('click', function () {
        const input = document.querySelector('.coupon-input input');
        if (input && input.value) {
            alert('Cupón aplicado: ' + input.value);
        }
    });
})();


// Calendario para envío planificado
function toggleDatePicker(event) {
    event.preventDefault();
    const datePicker = document.getElementById('deliveryDateTime');
    const link = event.target;

    if (datePicker.style.display === 'none') {
        datePicker.style.display = 'block';
        link.textContent = 'Ocultar calendario';

        // Establecer fecha mínima (mañana)
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        tomorrow.setHours(10, 0, 0, 0);

        const minDate = tomorrow.toISOString().slice(0, 16);
        datePicker.min = minDate;

        // Seleccionar automáticamente el radio de envío planificado
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
        if (!selectedRadio) return; // No hay opciones de envío en esta página

        const selectedValue = selectedRadio.value;

        shippingOptions.forEach(option => {
            const radio = option.querySelector('input[name="envio"]');
            if (radio && radio.value === selectedValue) {
                option.classList.add('active');
            } else {
                option.classList.remove('active');
            }
        });

        // Actualizar resumen (envío) según selección
        updateShippingFromSelection();
    }

    radios.forEach(radio => {
        radio.addEventListener('change', updateActiveState);
    });

    // Guardar el envío inicial seleccionado al cargar la página
    if (shippingOptions.length > 0 && radios.length > 0) {
        updateShippingFromSelection();
    }

    // Also handle the click on the link for "Envío Planificado"
    const planificadoLink = document.querySelector('.shipping-link');
    if (planificadoLink) {
        planificadoLink.addEventListener('click', function () {
            // The toggleDatePicker function already checks the radio.
            // We just need to call updateActiveState.
            setTimeout(updateActiveState, 0);
        });
    }

    // Initial state - solo si hay radios
    if (radios.length > 0) {
        updateActiveState();
    }
});



// Rellenar entrega con el primer producto del carrito (localStorage)
document.addEventListener('DOMContentLoaded', function () {
    var container = document.getElementById('deliveryProduct');
    if (!container) return;
    // Si el servidor ya pasó 'book', no hacemos nada (contenido ya renderizado)
    var hasServerBook = !!document.querySelector('.delivery-product-sku');
    if (hasServerBook) return;

    try {
        // Usar la misma clave que el resumen (base2): 'booklyCart'.
        // Fallback a la clave antigua 'bookly_cart' si está vacía.
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
            // Añadir autor y SKU si existen
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
        // Silencio: si falla, se mantiene el placeholder
    }
});


(function () {
    function fmt(n) { try { return new Intl.NumberFormat('es-CL').format(n || 0); } catch (e) { return (n || 0).toString(); } }
    
    function renderSummary() {
        var list = document.getElementById('summaryList');
        var subEl = document.getElementById('sumSubtotalBase2');
        var totEl = document.getElementById('sumTotalBase2');
        if (!list || !subEl || !totEl) return;
        var items = [];
        try {
            // Intentar con la clave nueva y hacer fallback a la antigua si está vacío
            var raw = localStorage.getItem('booklyCart');
            if (!raw || raw === '[]') {
                raw = localStorage.getItem('bookly_cart') || '[]';
            }
            items = JSON.parse(raw || '[]');
        } catch (e) {
            items = [];
        }
        list.innerHTML = '';
        if (!items.length) { list.innerHTML = '<p style="color:#666;">Tu carrito está vacío.</p>'; subEl.textContent = '$0'; totEl.textContent = '$2.990'; return; }
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
        var ivaRate = 0.19;
        var netSubtotal = Math.max(0, Math.round(gross * (1 - ivaRate)));
        var ivaAmount = Math.max(0, Math.round(gross * ivaRate));
        subEl.textContent = '$' + fmt(netSubtotal);
        var ivaEl = document.getElementById('sumIvaBase2');
        if (ivaEl) ivaEl.textContent = '$' + fmt(ivaAmount);
        
        // Restaurar envío desde localStorage ANTES de calcular el total
        var totalsBox = document.getElementById('summaryTotals');
        var envio = 0;
        if (totalsBox) {
            var shipEl = document.getElementById('sumShippingBase2');
            // Verificar si hay opciones de envío REALES (con radio name="envio")
            var hasShippingOptions = !!document.querySelector('input[name="envio"]');
            
            console.log('DEBUG - hasShippingOptions:', hasShippingOptions, 'shipEl:', shipEl);
            
            // Si no hay opciones de envío Y existe el elemento de envío, restaurar de localStorage
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
                // Leer del atributo data-shipping
                var ds = parseInt(totalsBox.getAttribute('data-shipping') || '0', 10);
                envio = isNaN(ds) ? 0 : ds;
            }
        }
        var total = gross + envio;
        totEl.textContent = '$' + fmt(total);
        console.log('Total calculado:', total, '(gross:', gross, '+ envío:', envio, ')');
        
        // Actualizar cuotas en base al total (6 cuotas sin interés)
        var installmentsEl = document.getElementById('installmentsText');
        if (installmentsEl && total > 0) {
            var installmentAmount = Math.round(total / 6);
            installmentsEl.textContent = 'hasta en 6 x $' + fmt(installmentAmount) + ' sin interés*';
        }
    }
    
    // Ejecutar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', renderSummary);
    } else {
        renderSummary();
    }
})();

// Lee el precio de la opción de envío seleccionada y actualiza el resumen
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
        // Guardar en localStorage para heredar en Pago
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
        // Recalcular total inmediato
        var totEl = document.getElementById('sumTotalBase2');
        var subEl = document.getElementById('sumSubtotalBase2');
        var ivaEl = document.getElementById('sumIvaBase2');
        if (!totEl || !subEl || !ivaEl) return;
        // Obtener gross a partir de neto + iva
        var net = parseInt(String(subEl.textContent).replace(/[^0-9]/g, ''), 10) || 0;
        var iva = parseInt(String(ivaEl.textContent).replace(/[^0-9]/g, ''), 10) || 0;
        var gross = net + iva;
        var total = gross + amount;
        totEl.textContent = '$' + new Intl.NumberFormat('es-CL').format(total);
        
        // Actualizar cuotas también cuando cambia el envío
        var installmentsEl = document.getElementById('installmentsText');
        if (installmentsEl && total > 0) {
            var installmentAmount = Math.round(total / 6);
            installmentsEl.textContent = 'hasta en 6 x $' + new Intl.NumberFormat('es-CL').format(installmentAmount) + ' sin interés*';
        }
    } catch (e) {
        console.error('Error en updateShippingFromSelection:', e);
    }
}

// Al cargar Pago (u otras páginas sin opciones de envío), restaurar del localStorage
document.addEventListener('DOMContentLoaded', function(){
    try {
        var totalsBox = document.getElementById('summaryTotals');
        if (!totalsBox) return;
        var hasShippingOptions = !!document.querySelector('.shipping-option');
        if (hasShippingOptions) return; // Ya se maneja con updateShippingFromSelection
        // Solo restaurar si la página muestra envío (tiene elemento #sumShippingBase2)
        var shipEl = document.getElementById('sumShippingBase2');
        if (!shipEl) return; // Checkout no debe mostrar envío
        var saved = parseInt(localStorage.getItem('booklyShipping') || '0', 10) || 0;
        console.log('Restaurando envío desde localStorage:', saved);
        if (saved > 0) {
            totalsBox.setAttribute('data-shipping', String(saved));
            shipEl.textContent = '$' + new Intl.NumberFormat('es-CL').format(saved);
            // Recalcular total
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

// Enviar el total (incluye envío) a Flow al presionar Pagar
document.addEventListener('DOMContentLoaded', function(){
    try {
        var pagarLink = document.getElementById('linkPagarFlow') || document.querySelector('.flow-actions a[href*="pago_create"]');
        var pagarBtn = document.getElementById('btnPagarFlow');
        if (!pagarLink) return;
        function handlePay(ev){
            ev.preventDefault();
            // Prevent double submissions
            try {
                if (pagarBtn) { pagarBtn.disabled = true; pagarBtn.style.pointerEvents = 'none'; }
                if (pagarLink) { pagarLink.style.pointerEvents = 'none'; }
            } catch(e) {}
            // Intentar leer el total mostrado en el resumen
            var totalEl = document.getElementById('sumTotalBase2');
            var total = 0;
            if (totalEl && totalEl.textContent) {
                total = parseInt(String(totalEl.textContent).replace(/[^0-9]/g, ''), 10) || 0;
            }
            // Fallback: calcular desde localStorage si fuese necesario
            if (total <= 0) {
                try {
                    var raw = localStorage.getItem('booklyCart');
                    if (!raw || raw === '[]') raw = localStorage.getItem('bookly_cart') || '[]';
                    var items = JSON.parse(raw || '[]');
                    var gross = 0;
                    items.forEach(function(it){ var q = parseInt(it.qty||1,10)||1; var p = parseInt(it.price||0,10)||0; gross += q*p; });
                    var ship = parseInt(localStorage.getItem('booklyShipping') || '0', 10) || 0;
                    total = gross + ship;
                } catch (e) {}
            }
            if (!total || total <= 0) {
                alert('No se pudo determinar el total a cobrar.');
                return;
            }
            var url = new URL(pagarLink.href, window.location.origin);
            url.searchParams.set('amount', String(total));
            window.location.href = url.toString();
        }
        pagarLink.addEventListener('click', handlePay);
        if (pagarBtn) pagarBtn.addEventListener('click', handlePay);
    } catch (e) { /* no-op */ }
});