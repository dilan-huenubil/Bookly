// Centralizado: funcionalidades compartidas para todas las páginas
// Se ejecutan de forma segura sólo si existen los elementos requeridos.

// 1. Menú móvil y búsqueda overlay
(function(){
	var toggle = document.querySelector('.mobile-menu-toggle');
	var overlay = document.getElementById('mobileOverlay');
	var closeBtn = document.getElementById('mobileClose');
	var overlayLinks = overlay ? overlay.querySelectorAll('a') : [];
	var searchBtn = document.querySelector('.mobile-search');
	var overlaySearchBtn = document.getElementById('overlaySearchBtn');
	var searchOverlay = document.getElementById('mobileSearch');
	var searchBack = document.getElementById('mobileSearchBack');
	var searchInput = document.getElementById('mobileSearchInput');

	function openMenu(){ if(!overlay) return; overlay.classList.add('open'); overlay.setAttribute('aria-hidden','false'); document.body.style.overflow='hidden'; }
	function closeMenu(){ if(!overlay) return; overlay.classList.remove('open'); overlay.setAttribute('aria-hidden','true'); document.body.style.overflow=''; }
	function openSearch(){ if(!searchOverlay) return; if(overlay && overlay.classList.contains('open')) closeMenu(); searchOverlay.classList.add('open'); searchOverlay.setAttribute('aria-hidden','false'); document.body.style.overflow='hidden'; setTimeout(function(){ if(searchInput) searchInput.focus(); },50); }
	function closeSearch(){ if(!searchOverlay) return; searchOverlay.classList.remove('open'); searchOverlay.setAttribute('aria-hidden','true'); document.body.style.overflow=''; }

	if(toggle) toggle.addEventListener('click', openMenu);
	if(closeBtn) closeBtn.addEventListener('click', closeMenu);
	if(overlayLinks.length) overlayLinks.forEach(function(l){ l.addEventListener('click', closeMenu); });
	if(searchBtn) searchBtn.addEventListener('click', openSearch);
	if(searchBack) searchBack.addEventListener('click', closeSearch);
	if(overlaySearchBtn) overlaySearchBtn.addEventListener('click', openSearch);
	document.addEventListener('keydown', function(e){ if(e.key==='Escape'){ closeMenu(); closeSearch(); } });
})();

// 2. Header sticky
(function(){
	var header = document.querySelector('header');
	if(!header) return;
	var lastState=false, headerHeight=header.offsetHeight;
	function setBodyOffset(add){ document.body.style.paddingTop = add ? headerHeight+'px' : ''; }
	function onResize(){ headerHeight = header.offsetHeight; if(header.classList.contains('is-sticky')) setBodyOffset(true); }
	function onScroll(){ var y = window.scrollY||window.pageYOffset||0; var shouldStick = y>10; if(shouldStick!==lastState){ lastState=shouldStick; if(shouldStick){ header.classList.add('is-sticky'); setBodyOffset(true); } else { header.classList.remove('is-sticky'); setBodyOffset(false); } } }
	window.addEventListener('scroll', onScroll, { passive:true });
	window.addEventListener('resize', onResize);
})();

// 3. Botón volver arriba
(function(){
	var btn = document.getElementById('backToTop');
	if(!btn) return;
	var last=false;
	// En páginas cortas como carrito, usa un umbral menor para mostrar el botón
	var isCartPage = !!document.querySelector('.cart-page');
	var threshold = isCartPage ? 50 : 250;
	function onScroll(){ var y=window.scrollY||window.pageYOffset||0; var show=y>threshold; if(show!==last){ last=show; btn.classList.toggle('show', show); } }
	btn.addEventListener('click', function(){ window.scrollTo({ top:0, behavior:'smooth' }); });
	window.addEventListener('scroll', onScroll, { passive:true });
})();

// 4. Filtro de precio (lista de productos)
(function(){
	var select = document.getElementById('priceFilter');
	var cards = Array.prototype.slice.call(document.querySelectorAll('.products .card'));
	if(!select || !cards.length) return;
	function normalizar(text){ if(!text) return 0; return parseInt(text.replace(/[^0-9]/g,''),10)||0; }
	function precio(card){ var span=card.querySelector('p span'); return normalizar(span?span.textContent:'0'); }
	function cumple(v,r){ switch(r){ case '0-15000': return v<=15000; case '15000-30000': return v>15000 && v<=30000; case '30000-60000': return v>30000 && v<=60000; case '60000-plus': return v>60000; default: return true; } }
	function aplicar(){ var r=select.value; cards.forEach(function(c){ var p=precio(c); c.style.display = cumple(p,r)?'':'none'; }); }
	select.addEventListener('change', aplicar);
})();

// 5. Carrito lateral (drawer)
(function(){
	var drawer=document.getElementById('cartDrawer');
	var backdrop=document.getElementById('cartBackdrop');
	var toggles=document.querySelectorAll('[data-cart-toggle]');
	var closeBtn=document.getElementById('cartClose');
	var continueBtn=document.getElementById('cartContinue');
	var checkoutBtnDrawer=document.getElementById('cartCheckout');
	var cartBody=document.getElementById('cartBody');
	var cartEmptyMsg=document.getElementById('cartEmptyMsg');
	var cartActions=document.getElementById('cartActions');
	var cartItems=document.getElementById('cartItems');
	var cartTotals=document.getElementById('cartTotals');
	var subtotalEl=document.getElementById('cartSubtotal');
	var totalEl=document.getElementById('cartTotal');
	if(!drawer||!backdrop||!toggles.length) return;
	var previousFocus=null;
	var focusableSel='a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])';
	function lockScroll(b){ document.body.style.overflow = b?'hidden':''; }
	function closeOther(){ var menu=document.getElementById('mobileOverlay'); var search=document.getElementById('mobileSearch'); if(menu){ menu.classList.remove('open'); menu.setAttribute('aria-hidden','true'); } if(search){ search.classList.remove('open'); search.setAttribute('aria-hidden','true'); } }
	function open(){ closeOther(); previousFocus=document.activeElement; try { renderCart(); } catch(e){}; drawer.classList.add('open'); drawer.setAttribute('aria-hidden','false'); backdrop.classList.add('show'); backdrop.setAttribute('aria-hidden','false'); lockScroll(true); var first=drawer.querySelector(focusableSel); if(first) first.focus(); }
	function close(){ drawer.classList.remove('open'); drawer.setAttribute('aria-hidden','true'); backdrop.classList.remove('show'); backdrop.setAttribute('aria-hidden','true'); lockScroll(false); if(previousFocus && previousFocus.focus) previousFocus.focus(); }
	function onKey(e){ if(e.key==='Escape') return close(); if(e.key==='Tab' && drawer.classList.contains('open')){ var items=drawer.querySelectorAll(focusableSel); if(!items.length) return; var first=items[0], last=items[items.length-1]; if(e.shiftKey && document.activeElement===first){ e.preventDefault(); last.focus(); } else if(!e.shiftKey && document.activeElement===last){ e.preventDefault(); first.focus(); } } }
	toggles.forEach(function(trigger){
		trigger.addEventListener('click', function(e){
			e.preventDefault();
			open();
		});
		trigger.addEventListener('keydown', function(e){ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); open(); } });
	});
	if(closeBtn) closeBtn.addEventListener('click', close);
	if(continueBtn) continueBtn.addEventListener('click', close);
	if(checkoutBtnDrawer) checkoutBtnDrawer.addEventListener('click', function(e){
		// Navega usando href/data-url si existe; fallback a ruta Django
		var href = checkoutBtnDrawer.getAttribute('href') || checkoutBtnDrawer.dataset.url || '/carrito/';
		e.preventDefault();
		window.location.href = href;
	});
	backdrop.addEventListener('click', close);
	document.addEventListener('keydown', onKey);

	// --- Lógica de carrito ---
	function formatCL(num){ try { return new Intl.NumberFormat('es-CL').format(num||0); } catch(e){ return (num||0).toString(); } }
	function getCart(){ try { return JSON.parse(localStorage.getItem('booklyCart')||'[]'); } catch(e){ return []; } }
	function saveCart(items){ localStorage.setItem('booklyCart', JSON.stringify(items||[])); }
	function renderCart(){ if(!cartBody) return; var items=getCart(); if(cartItems) cartItems.innerHTML=''; var subtotal=0; var totalQty=0; items.forEach(function(it, idx){ var qty=(parseInt(it.qty,10)||1); totalQty += qty; var line= (it.price||0) * qty; subtotal += line; var row=document.createElement('div'); row.className='cart-item'; row.setAttribute('data-sku', it.sku);
			row.innerHTML = '<img src="'+(it.image||'https://via.placeholder.com/80x80')+'" alt="Item" />'
				+'<div class="ci-meta">'
			+'<p class="ci-name">'+(it.title||'Producto')+'</p>'
			+'<p class="ci-price">'+(it.qty||1)+' x $'+formatCL(it.price||0)+'</p>'
			+'</div>'
			+'<button class="ci-remove" aria-label="Eliminar"><i class="bi bi-trash"></i></button>';
		var removeBtn = row.querySelector('.ci-remove');
		removeBtn.addEventListener('click', function(){ 
			var arr=getCart(); 
			var i = arr.findIndex(function(x){ return x.sku===it.sku; }); 
			if(i>-1){ 
				arr.splice(i,1); 
				saveCart(arr); 
				renderCart();
				// Si estamos en carrito.html, actualizar la tabla también
				if(typeof window.refreshCartPage === 'function') window.refreshCartPage();
			} 
		});
		if(cartItems) cartItems.appendChild(row);
		});
		// Mostrar/ocultar mensaje y acciones según vacío
		if(cartEmptyMsg) cartEmptyMsg.style.display = items.length ? 'none' : 'block';
		if(cartActions) cartActions.style.display = items.length ? '' : 'none';
		if(cartTotals) cartTotals.style.display = items.length ? '' : 'none';
		var ivaRate = 0.19;
		var netSubtotal = Math.max(0, Math.round(subtotal * (1 - ivaRate)));
		if(subtotalEl) subtotalEl.textContent = '$'+formatCL(netSubtotal);
		if(totalEl) totalEl.textContent = '$'+formatCL(subtotal); // total bruto (con IVA)
		// Actualizar metadatos del icono del carrito (desktop y mobile)
		var desktopIcon = document.getElementById('cartToggle');
		var mobileBtns = document.querySelectorAll('.mobile-cart, .overlay-cart-btn');
		var labelText = items.length ? ('Abrir carrito ('+totalQty+' ítems)') : 'Abrir carrito (vacío)';
		var titleText = items.length ? (totalQty+' ítems en el carrito') : 'Carrito vacío';
		var countText = String(totalQty);
		if(desktopIcon){ desktopIcon.setAttribute('aria-label', labelText); desktopIcon.title = titleText; desktopIcon.setAttribute('data-count', countText); }
		mobileBtns.forEach(function(btn){ btn.setAttribute('aria-label', labelText); btn.title = titleText; btn.setAttribute('data-count', countText); });
	}
	function addToCart(item){ var arr=getCart(); var existing = arr.find(function(x){ return x.sku===item.sku; }); if(existing){ existing.qty = (existing.qty||1) + (item.qty||1); } else { arr.push({ sku:item.sku, title:item.title, price:item.price, image:item.image, qty:item.qty||1 }); } saveCart(arr); renderCart(); }
	// Exponer helper global para páginas que quieran agregar y abrir
	window.BooklyCartAdd = function(item){ addToCart(item); open(); };
	renderCart();

	// Delegar clicks en botones "AGREGAR AL CARRITO" de listados
	document.addEventListener('click', function(e){ var btn = e.target.closest('button.add-to-cart'); if(!btn) return; var card = btn.closest('.card'); if(!card) return; var sku = card.getAttribute('data-sku'); var title = card.getAttribute('data-title') || (card.querySelector('h3') && card.querySelector('h3').textContent) || 'Producto'; var priceAttr = card.getAttribute('data-price'); var price = parseInt(priceAttr,10); if(isNaN(price)){ var pText = (card.querySelector('.price') && card.querySelector('.price').textContent) || '0'; price = parseInt(String(pText).replace(/[^0-9]/g,''),10)||0; } var imgEl = card.querySelector('img'); var image = card.getAttribute('data-image') || (imgEl && imgEl.getAttribute('src')) || ''; addToCart({ sku: sku||title, title: title, price: price, image: image, qty: 1 }); open(); });
})();

// 6. Tabs de descripción (solo páginas con #tabs)
(function(){
	if(!document.getElementById('tabs')) return; // no existe en todas las páginas
	var btnDesc=document.getElementById('btn-description');
	var btnAdd=document.getElementById('btn-additional');
	var tabDesc=document.getElementById('tab-description');
	var tabAdd=document.getElementById('tab-additional');
	function activate(target){ var isDesc = target==='desc'; if(btnDesc) btnDesc.classList.toggle('active', isDesc); if(btnAdd) btnAdd.classList.toggle('active', !isDesc); if(tabDesc){ tabDesc.classList.toggle('show', isDesc); tabDesc.hidden=!isDesc; } if(tabAdd){ tabAdd.classList.toggle('show', !isDesc); tabAdd.hidden=isDesc; } if(btnDesc && btnAdd){ if(isDesc){ btnDesc.setAttribute('aria-selected','true'); btnAdd.setAttribute('aria-selected','false'); } else { btnDesc.setAttribute('aria-selected','false'); btnAdd.setAttribute('aria-selected','true'); } } }
	if(btnDesc) btnDesc.addEventListener('click', function(){ activate('desc'); });
	if(btnAdd) btnAdd.addEventListener('click', function(){ activate('add'); });
})();

// 7. Cantidad +/- y abrir carrito al agregar (páginas de producto)
(function(){
	var minus=document.querySelector('.qty-btn[data-op="-"]');
	var plus=document.querySelector('.qty-btn[data-op="+"]');
	var input=document.getElementById('qtyInput');
	if(!minus && !plus && !input) return; // no está en todas las páginas
	function clamp(){ var v=parseInt((input && input.value)||'1',10); if(isNaN(v)||v<1) v=1; if(input) input.value=v; }
	if(minus) minus.addEventListener('click', function(){ clamp(); var v=parseInt(input.value,10); if(v>1) input.value=v-1; });
	if(plus) plus.addEventListener('click', function(){ clamp(); input.value=parseInt(input.value,10)+1; });
	if(input) input.addEventListener('change', clamp);
	if(input){ input.addEventListener('wheel', function(e){ e.preventDefault(); }, { passive:false }); input.addEventListener('keydown', function(e){ e.preventDefault(); }); }
	var add=document.getElementById('addToCart');
	if(add){ add.addEventListener('click', function(){
		var titleEl = document.querySelector('.ph-title');
		var priceEl = document.querySelector('.ph-price-block .price');
		var imgEl = document.querySelector('.ph-gallery img');
		var skuEl = document.querySelector('.ph-extra strong');
		var title = titleEl ? titleEl.textContent : 'Producto';
		var price = 0; if(priceEl){ price = parseInt(String(priceEl.textContent).replace(/[^0-9]/g,''),10)||0; }
		var image = imgEl ? imgEl.getAttribute('src') : '';
		var sku = skuEl ? skuEl.textContent : title;
		var qty = input ? parseInt(input.value,10)||1 : 1;
		if(window.BooklyCartAdd){ window.BooklyCartAdd({ sku: sku, title: title, price: price, image: image, qty: qty }); }
	}); }
})();



// 9. Página de carrito (carrito.html) - lógica básica
(function(){
	var cartPage = document.querySelector('.cart-page');
	if(!cartPage) return; // Sólo en carrito.html

	var tbody = document.getElementById('cartRows');
	var subtotalEl = document.getElementById('sumSubtotal');
	var totalEl = document.getElementById('sumTotal');
	var checkoutBtn = document.getElementById('btnCheckout');
	var couponBtn = document.getElementById('btnApplyCoupon');
	var couponInput = document.getElementById('couponInput');
	var appliedCoupon = null; // { code, discountType, value }

	function getCart(){ try { return JSON.parse(localStorage.getItem('booklyCart')||'[]'); } catch(e){ return []; } }
	function saveCart(items){ localStorage.setItem('booklyCart', JSON.stringify(items||[])); }
	function formatCL(num){ return new Intl.NumberFormat('es-CL').format(num||0); }

	function renderRows(){ if(!tbody) return; tbody.innerHTML=''; var items=getCart(); items.forEach(function(it){ var tr=document.createElement('tr'); tr.className='row-item'; tr.setAttribute('data-sku', it.sku); tr.setAttribute('data-price', it.price||0);
			tr.innerHTML = '<td class="td-producto">'
				+'<div class="prod">'
				+'<button class="remove" aria-label="Eliminar"><i class="bi bi-x"></i></button>'
				+'<img src="'+(it.image||'https://via.placeholder.com/80x80')+'" alt="'+(it.title||'Producto')+'"/>'
				+'<div class="meta">'
				+'<a href="#" class="name">'+(it.title||'Producto')+'</a>'
				+'<div class="price-detail">Precio Internet: <span class="now">$'+formatCL(it.price||0)+'</span></div>'
				+'</div>'
				+'</div>'
				+'</td>'
				+'<td class="td-precio">$'+formatCL(it.price||0)+'</td>'
				+'<td class="td-cantidad">'
				+'<div class="qty qty-cart">'
				+'<button class="qty-btn" data-op="-" aria-label="Disminuir">-</button>'
				+'<input type="number" class="qty-input" min="1" value="'+(it.qty||1)+'" aria-label="Cantidad"/>'
				+'<button class="qty-btn" data-op="+" aria-label="Aumentar">+</button>'
				+'</div>'
				+'</td>'
				+'<td class="td-subtotal">$'+formatCL((it.price||0)*(it.qty||1))+'</td>'
				+'<td class="td-remove"></td>';
			bindRow(tr);
			tbody.appendChild(tr);
		});
		recalc();
		updateEmptyState();
	}
	
	// Exponer renderRows globalmente para sincronización con drawer
	window.refreshCartPage = renderRows;

	function recalc(){ var rows = tbody ? tbody.querySelectorAll('tr.row-item') : []; var gross = 0; var ivaRate = 0.19; rows.forEach(function(r){ var base = parseInt(r.getAttribute('data-price'),10)||0; var qtyInput = r.querySelector('.qty-input'); var qty = parseInt(qtyInput && qtyInput.value,10) || 1; var line = base * qty; gross += line; var netLine = Math.max(0, Math.round(line * (1 - ivaRate))); var cell = r.querySelector('.td-subtotal'); if(cell) cell.textContent = '$'+formatCL(netLine); }); if(appliedCoupon){ if(appliedCoupon.discountType === 'percent'){ gross = Math.round(gross * (1 - appliedCoupon.value/100)); } else if(appliedCoupon.discountType === 'fixed') { gross = Math.max(0, gross - appliedCoupon.value); } } var netSubtotal = Math.max(0, Math.round(gross * (1 - ivaRate))); if(subtotalEl) subtotalEl.textContent = '$'+formatCL(netSubtotal); if(totalEl) totalEl.textContent = '$'+formatCL(gross); if(checkoutBtn) checkoutBtn.disabled = gross === 0; }

	function updateEmptyState(){
		var items=getCart();
		var emptyMsg = document.getElementById('cartPageEmptyMsg');
		var totalsRow = document.getElementById('cartPageTotals');
		var checkoutBtnEl = document.getElementById('btnCheckout');
		// Importante: ocultar sólo el contenedor de la tabla para no ocultar el mensaje
		var tableWrapEl = document.querySelector('.cart-table .table-wrap');
		var summaryAside = document.getElementById('cartSummary');
		var cartPageEl = document.querySelector('.cart-page');
		var isEmpty = !items.length;
		if(emptyMsg) emptyMsg.style.display = isEmpty ? 'block' : 'none';
		if(tableWrapEl) tableWrapEl.style.display = isEmpty ? 'none' : '';
		if(summaryAside) summaryAside.style.display = isEmpty ? 'none' : '';
		// Añade clase para mantener altura y evitar que el footer suba
		if(cartPageEl) cartPageEl.classList.toggle('empty', isEmpty);
		// Totales y CTA también quedan ocultos por ocultar el aside
		if(totalsRow) totalsRow.style.display = isEmpty ? 'none' : '';
		if(checkoutBtnEl) checkoutBtnEl.style.display = isEmpty ? 'none' : '';
		updateCartIconMeta();
	}

	function bindRow(row){ var minus = row.querySelector('.qty-btn[data-op="-"]'); var plus = row.querySelector('.qty-btn[data-op="+"]'); var input = row.querySelector('.qty-input'); var removeBtn = row.querySelector('.remove'); function clamp(){ var v=parseInt(input.value,10); if(isNaN(v)||v<1) v=1; input.value=v; }
		if(minus) minus.addEventListener('click', function(){ clamp(); var v=parseInt(input.value,10); if(v>1) input.value=v-1; syncRow(row); });
		if(plus) plus.addEventListener('click', function(){ clamp(); input.value=parseInt(input.value,10)+1; syncRow(row); });
		if(input) input.addEventListener('change', function(){ clamp(); syncRow(row); });
		if(removeBtn) removeBtn.addEventListener('click', function(){ var sku=row.getAttribute('data-sku'); var arr=getCart(); var i=arr.findIndex(function(x){ return x.sku===sku; }); if(i>-1){ arr.splice(i,1); saveCart(arr); renderRows(); updateEmptyState(); } });
	}

	function syncRow(row){ var sku=row.getAttribute('data-sku'); var arr=getCart(); var it = arr.find(function(x){ return x.sku===sku; }); var input = row.querySelector('.qty-input'); var qty = parseInt(input && input.value,10)||1; if(it){ it.qty = qty; saveCart(arr); } recalc(); updateCartIconMeta(); }

	// Actualiza el badge del icono del carrito (desktop y mobile)
	function updateCartIconMeta(){
		var items=getCart(); var totalQty=0; items.forEach(function(it){ totalQty += (parseInt(it.qty,10)||1); });
		var desktopIcon = document.getElementById('cartToggle');
		var mobileBtns = document.querySelectorAll('.mobile-cart, .overlay-cart-btn');
		var labelText = items.length ? ('Abrir carrito ('+totalQty+' ítems)') : 'Abrir carrito (vacío)';
		var titleText = items.length ? (totalQty+' ítems en el carrito') : 'Carrito vacío';
		var countText = String(totalQty);
		if(desktopIcon){ desktopIcon.setAttribute('aria-label', labelText); desktopIcon.title = titleText; desktopIcon.setAttribute('data-count', countText); }
		mobileBtns.forEach(function(btn){ btn.setAttribute('aria-label', labelText); btn.title = titleText; btn.setAttribute('data-count', countText); });
	}

	if(couponBtn){ couponBtn.addEventListener('click', function(e){ e.preventDefault(); var code = (couponInput && couponInput.value || '').trim().toUpperCase(); if(!code){ alert('Ingrese un código de cupón.'); return; } if(code === 'DESCUENTO10'){ appliedCoupon = { code: code, discountType: 'percent', value: 10 }; alert('Cupón aplicado: 10%'); } else if(code === 'MENOS2000') { appliedCoupon = { code: code, discountType: 'fixed', value: 2000 }; alert('Cupón aplicado: -$2.000'); } else { appliedCoupon = null; alert('Cupón inválido o no reconocido (demo).'); } recalc(); }); }

	renderRows();
	updateEmptyState();
})();



// ==========================
// FUNCIONES GENERALES
// ==========================

// Crear o actualizar mensaje de error debajo del input
function setFieldError(input, message) {
    removeFieldError(input);

    const error = document.createElement("p");
    error.className = "msg-error";
    error.innerText = message;
    input.insertAdjacentElement("afterend", error);
    input.classList.add("input-error");
}

// Borrar error del input
function removeFieldError(input) {
    const next = input.nextElementSibling;
    if (next && next.classList.contains("msg-error")) {
        next.remove();
    }
    input.classList.remove("input-error");
}

// Email válido
function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// Validar mayúscula y carácter especial
function validateStrongPassword(pass) {
    const hasUpper = /[A-Z]/.test(pass);
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>_\-]/.test(pass);
    return {
        upper: hasUpper,
        special: hasSpecial
    };
}


// ==========================
// VALIDACIÓN EN TIEMPO REAL - LOGIN
// ==========================
document.getElementById("loginUser").addEventListener("input", function() {
    if (this.value.trim() === "") {
        setFieldError(this, "Debes ingresar tu usuario o correo");
    } else {
        removeFieldError(this);
    }
});

document.getElementById("loginPass").addEventListener("input", function() {
    if (this.value.trim() === "") {
        setFieldError(this, "Debes ingresar tu contraseña");
    } else {
        removeFieldError(this);
    }
});


// ==========================
// VALIDACIÓN EN TIEMPO REAL - REGISTRO
// ==========================
document.getElementById("regUser").addEventListener("input", function() {
    if (this.value.trim().length < 3) {
        setFieldError(this, "El nombre de usuario debe tener al menos 3 caracteres");
    } else {
        removeFieldError(this);
    }
});

document.getElementById("regEmail").addEventListener("input", function() {
    const email = this.value.trim();

    if (email === "") {
        setFieldError(this, "El correo es obligatorio");
        return;
    }

    if (!validateEmail(email)) {
        setFieldError(this, "El correo no es válido");
        return;
    }

    removeFieldError(this);
});


document.getElementById("regPass1").addEventListener("input", function() {
    const pass = this.value.trim();
    const strong = validateStrongPassword(pass);

    // 1) Campo vacío
    if (pass === "") {
        setFieldError(this, "La contraseña es obligatoria");
        return;
    }

    // 2) Largo mínimo
    if (pass.length < 8) {
        setFieldError(this, "Debe tener al menos 8 caracteres");
        return;
    }

    // 3) Mayúscula
    if (!strong.upper) {
        setFieldError(this, "Debe incluir al menos UNA mayúscula");
        return;
    }

    // 4) Carácter especial
    if (!strong.special) {
        setFieldError(this, "Debe incluir al menos UN carácter especial (! @ # $ % ...)");
        return;
    }

    // Todo OK
    removeFieldError(this);
});


document.getElementById("regPass2").addEventListener("input", function() {
    const pass1 = document.getElementById("regPass1").value.trim();
    const pass2 = this.value.trim();

    if (pass2 === "") {
        setFieldError(this, "Debes confirmar la contraseña");
        return;
    }

    if (pass2 !== pass1) {
        setFieldError(this, "Las contraseñas no coinciden");
        return;
    }

    removeFieldError(this);
});



// ==========================
// VALIDACIÓN FINAL AL ENVIAR (LOGIN)
// ==========================
document.getElementById("loginForm").addEventListener("submit", function(e) {
    let valid = true;

    const user = document.getElementById("loginUser");
    const pass = document.getElementById("loginPass");

    if (user.value.trim() === "") {
        setFieldError(user, "Debes ingresar tu usuario o correo");
        valid = false;
    }
    if (pass.value.trim() === "") {
        setFieldError(pass, "Debes ingresar tu contraseña");
        valid = false;
    }

    if (!valid) e.preventDefault();
});



// ==========================
// VALIDACIÓN FINAL AL ENVIAR (REGISTRO)
// ==========================
document.getElementById("registerForm").addEventListener("submit", function(e) {
    let valid = true;

    const user = document.getElementById("regUser");
    const email = document.getElementById("regEmail");
    const pass1 = document.getElementById("regPass1");
    const pass2 = document.getElementById("regPass2");

    const pass = pass1.value.trim();
    const strong = validateStrongPassword(pass);

    // Usuario
    if (user.value.trim().length < 3) {
        setFieldError(user, "El nombre de usuario debe tener al menos 3 caracteres");
        valid = false;
    }

    // Email vacío
    if (email.value.trim() === "") {
        setFieldError(email, "El correo es obligatorio");
        valid = false;
    
    // Email con formato incorrecto
    } else if (!validateEmail(email.value.trim())) {
        setFieldError(email, "El correo no es válido");
        valid = false;
    }


    // Contraseña VACÍA
    if (pass === "") {
        setFieldError(pass1, "La contraseña es obligatoria");
        valid = false;

    // Largo
    } else if (pass.length < 8) {
        setFieldError(pass1, "Debe tener al menos 8 caracteres");
        valid = false;

    // Mayúscula
    } else if (!strong.upper) {
        setFieldError(pass1, "Debe incluir al menos UNA mayúscula");
        valid = false;

    // Carácter especial
    } else if (!strong.special) {
        setFieldError(pass1, "Debe incluir al menos UN carácter especial (! @ # $ % ...)");
        valid = false;
    }

    // Confirmación VACÍA
    if (pass2.value.trim() === "") {
        setFieldError(pass2, "Debes confirmar la contraseña");
        valid = false;
    
    // Confirmación distinta
    } else if (pass2.value !== pass1.value) {
        setFieldError(pass2, "Las contraseñas no coinciden");
        valid = false;
    }

    if (!valid) e.preventDefault();
});



