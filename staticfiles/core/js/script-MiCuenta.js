// =========================
// ACORDEÓN MIS COMPRAS (Página Mi Cuenta)
// =========================
document.addEventListener('DOMContentLoaded', () => {
    const userMenu = document.querySelector('.js-cuenta-user-menu');
    const userToggle = document.querySelector('.js-cuenta-user-toggle');
    const userClose = document.querySelector('.js-cuenta-user-close');

    if (userMenu && userToggle) {
        userToggle.addEventListener('click', (event) => {
            event.stopPropagation();
            const isOpen = userMenu.classList.toggle('is-open');
            userToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        });

        if (userClose) {
            userClose.addEventListener('click', (event) => {
                event.stopPropagation();
                userMenu.classList.remove('is-open');
                userToggle.setAttribute('aria-expanded', 'false');
            });
        }

        document.addEventListener('click', (event) => {
            if (!userMenu.contains(event.target)) {
                userMenu.classList.remove('is-open');
                userToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }

    const purchaseCards = document.querySelectorAll('.js-purchase-card');

    purchaseCards.forEach(card => {
        const toggleHeader = card.querySelector('.js-purchase-toggle');
        if (toggleHeader) {
            toggleHeader.addEventListener('click', () => {
                card.classList.toggle('is-open');
            });
        }
    });
});



document.addEventListener('DOMContentLoaded', () => {
    // Escucha de clics dinámica para botones de seguimiento
    document.addEventListener('click', function (e) {

        // Abrir seguimiento
        const trackToggle = e.target.closest('.js-track-toggle');
        if (trackToggle) {
            e.preventDefault();
            const body = trackToggle.closest('.purchase-body');
            const trackingContainer = body.querySelector('.js-tracking-container');
            if (trackingContainer) {
                trackingContainer.style.display = 'block';
            }
        }

        // Cerrar seguimiento
        const trackClose = e.target.closest('.js-track-close');
        if (trackClose) {
            e.preventDefault();
            const trackingContainer = trackClose.closest('.js-tracking-container');
            if (trackingContainer) {
                trackingContainer.style.display = 'none';
            }
        }
    });
});



// =========================
// VALIDACIÓN DE CAMBIOS Y DIRECCIONES EN MI PERFIL
// =========================
document.addEventListener('DOMContentLoaded', () => {
    const profileForm = document.querySelector('.profile-form');

    // Solo ejecutamos esto si estamos en la página de Mi Perfil
    if (profileForm) {
        // Inicializar regiones de Chile si la función está disponible
        if (typeof window.initChileRegions === 'function') {
            window.initChileRegions('regionSelect', 'comunaSelect');
        }

        const saveButton = profileForm.querySelector('button[type="submit"]');
        const inputs = profileForm.querySelectorAll('input:not([name="csrfmiddlewaretoken"]), select');

        // 1. Guardar los valores iniciales al cargar la página
        const initialValues = {};
        const snapshotInitial = () => {
            inputs.forEach(input => {
                if (input.type === 'checkbox') {
                    initialValues[input.name] = input.checked;
                } else {
                    initialValues[input.name] = input.value;
                }
            });
        };
        snapshotInitial();

        // 2. Función que compara los valores actuales con los iniciales
        let forceChanged = false;
        const checkChanges = () => {
            if (forceChanged) {
                saveButton.disabled = false;
                return;
            }
            let hasChanged = false;
            inputs.forEach(input => {
                if (input.type === 'checkbox') {
                    if (input.checked !== initialValues[input.name]) hasChanged = true;
                } else {
                    if (input.value !== initialValues[input.name]) hasChanged = true;
                }
            });

            // Habilita el botón si hay cambios, lo deshabilita si está igual
            saveButton.disabled = !hasChanged;
        };

        // 3. Ejecutar la validación inicial para deshabilitarlo al entrar
        setTimeout(() => {
            snapshotInitial();
            checkChanges();
        }, 80);

        // 4. Escuchar cada vez que el usuario escribe o cambia una opción
        inputs.forEach(input => {
            input.addEventListener('input', checkChanges);
            input.addEventListener('change', checkChanges);
        });

        // 5. Interacción de Direcciones Guardadas y Casillas Desplegables
        const addressEditorContainer = document.getElementById('addressEditorContainer');
        const addressEditorTitle = document.getElementById('addressEditorTitle');
        const addressActiveInput = document.getElementById('id_address_active');
        const btnCancelarDireccion = document.getElementById('btnCancelarDireccion');
        const btnAgregarPrimeraDireccion = document.getElementById('btnAgregarPrimeraDireccion');
        const btnNuevaDireccion = document.getElementById('btnNuevaDireccion');

        const addressIdInput = document.getElementById('id_address_id');
        const streetInput = document.getElementById('id_street');
        const numberInput = document.getElementById('id_number');
        const line2Input = document.getElementById('id_line2');
        const postalInput = document.getElementById('id_postal_code');
        const regionSelect = document.getElementById('regionSelect');
        const comunaSelect = document.getElementById('comunaSelect');
        const isDefaultCheckbox = document.getElementById('id_is_default');
        const addressChips = document.querySelectorAll('.profile-address-chip');

        const requiredAddressInputs = [
            { el: streetInput, name: 'Calle', errId: 'err_street' },
            { el: numberInput, name: 'Número', errId: 'err_number' },
            { el: postalInput, name: 'Código postal', errId: 'err_postal_code' },
            { el: regionSelect, name: 'Región', errId: 'err_region' },
            { el: comunaSelect, name: 'Comuna', errId: 'err_comuna' }
        ];

        const clearAddressErrors = () => {
            requiredAddressInputs.forEach(item => {
                if (item.el) item.el.classList.remove('is-invalid');
                const errSpan = document.getElementById(item.errId);
                if (errSpan) errSpan.style.display = 'none';
            });
        };

        const closeAddressEditor = () => {
            if (addressEditorContainer) addressEditorContainer.style.display = 'none';
            if (addressActiveInput) addressActiveInput.value = '0';
            clearAddressErrors();
            addressChips.forEach(chip => chip.classList.remove('is-active'));
            checkChanges();
        };

        const openAddressEditor = (isNew, chip = null) => {
            clearAddressErrors();
            const currentTotal = document.querySelectorAll('.profile-address-chip').length;

            if (isNew) {
                // Validación de límite máximo de 2 direcciones
                if (currentTotal >= 2) {
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            title: 'Límite alcanzado',
                            text: 'Solo puedes tener un máximo de 2 direcciones guardadas. Debes editar o eliminar una existente para agregar otra.',
                            icon: 'info',
                            confirmButtonColor: '#A65D37',
                            confirmButtonText: 'Entendido'
                        });
                    } else {
                        alert('Solo puedes tener un máximo de 2 direcciones guardadas.');
                    }
                    return;
                }

                if (addressEditorTitle) {
                    addressEditorTitle.innerHTML = '<i class="bi bi-plus-circle"></i> Nueva dirección de despacho';
                }
                if (addressIdInput) addressIdInput.value = '';
                if (streetInput) streetInput.value = '';
                if (numberInput) numberInput.value = '';
                if (line2Input) line2Input.value = '';
                if (postalInput) postalInput.value = '';
                if (isDefaultCheckbox) isDefaultCheckbox.checked = (currentTotal === 0);

                if (regionSelect) {
                    regionSelect.value = '';
                    regionSelect.dispatchEvent(new Event('change'));
                }
                if (comunaSelect) comunaSelect.value = '';

                addressChips.forEach(c => c.classList.remove('is-active'));
            } else if (chip) {
                if (addressEditorTitle) {
                    addressEditorTitle.innerHTML = '<i class="bi bi-pencil-square"></i> Editar dirección';
                }
                addressChips.forEach(c => c.classList.remove('is-active'));
                chip.classList.add('is-active');

                const streetFull = chip.dataset.street || '';
                const parts = streetFull.trim().split(/\s+/);
                if (parts.length > 1 && /^[\d\-]+[a-zA-Z]?$/.test(parts[parts.length - 1])) {
                    if (numberInput) numberInput.value = parts.pop();
                    if (streetInput) streetInput.value = parts.join(' ');
                } else {
                    if (streetInput) streetInput.value = streetFull;
                    if (numberInput) numberInput.value = '';
                }

                if (addressIdInput) addressIdInput.value = chip.dataset.id || '';
                if (line2Input) line2Input.value = chip.dataset.line2 || '';
                if (postalInput) postalInput.value = chip.dataset.postal || '';

                if (regionSelect && chip.dataset.region) {
                    regionSelect.value = chip.dataset.region;
                    regionSelect.dispatchEvent(new Event('change'));
                    if (comunaSelect && chip.dataset.comuna) {
                        setTimeout(() => {
                            comunaSelect.value = chip.dataset.comuna;
                            checkChanges();
                        }, 20);
                    }
                }

                if (isDefaultCheckbox) {
                    isDefaultCheckbox.checked = (chip.dataset.isDefault === 'true');
                }
            }

            if (addressActiveInput) addressActiveInput.value = '1';
            if (addressEditorContainer) addressEditorContainer.style.display = 'block';
            saveButton.disabled = false;

            if (streetInput) {
                streetInput.focus();
                streetInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        };

        if (btnNuevaDireccion) {
            btnNuevaDireccion.addEventListener('click', (e) => {
                e.preventDefault();
                openAddressEditor(true);
            });
        }

        if (btnAgregarPrimeraDireccion) {
            btnAgregarPrimeraDireccion.addEventListener('click', (e) => {
                e.preventDefault();
                openAddressEditor(true);
            });
        }

        if (btnCancelarDireccion) {
            btnCancelarDireccion.addEventListener('click', (e) => {
                e.preventDefault();
                closeAddressEditor();
            });
        }

        // Selección y edición de una dirección existente desde las tarjetas
        document.querySelectorAll('.js-select-address').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = btn.dataset.target;
                const chip = targetId ? document.getElementById(targetId) : btn.closest('.profile-address-chip');
                if (chip) openAddressEditor(false, chip);
            });
        });

        // 6. Eliminar dirección (vía formulario externo seguro)
        document.querySelectorAll('.js-delete-addr').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const url = btn.dataset.url;
                if (!url) return;

                const executeDelete = () => {
                    const actionForm = document.getElementById('addressActionForm');
                    if (actionForm) {
                        actionForm.action = url;
                        actionForm.submit();
                    }
                };

                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        title: '¿Eliminar dirección?',
                        text: 'Esta dirección ya no estará disponible para tus compras.',
                        icon: 'warning',
                        showCancelButton: true,
                        confirmButtonColor: '#B94A3A',
                        cancelButtonColor: '#7A6E65',
                        confirmButtonText: 'Sí, eliminar',
                        cancelButtonText: 'Cancelar'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            executeDelete();
                        }
                    });
                } else {
                    if (confirm('¿Deseas eliminar esta dirección de despacho?')) {
                        executeDelete();
                    }
                }
            });
        });

        // 7. Establecer dirección principal (mediante radio buttons o botones)
        document.querySelectorAll('.js-select-main-addr').forEach(radio => {
            radio.addEventListener('change', (e) => {
                const url = radio.dataset.url;
                if (!url) return;

                const actionForm = document.getElementById('addressActionForm');
                if (actionForm) {
                    actionForm.action = url;
                    actionForm.submit();
                }
            });
        });

        document.querySelectorAll('.js-set-default-addr').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const url = btn.dataset.url;
                if (!url) return;

                const actionForm = document.getElementById('addressActionForm');
                if (actionForm) {
                    actionForm.action = url;
                    actionForm.submit();
                }
            });
        });

        // 8. Limpiar errores visuales al escribir o seleccionar
        requiredAddressInputs.forEach(item => {
            if (item.el) {
                const clearErr = () => {
                    item.el.classList.remove('is-invalid');
                    const errSpan = document.getElementById(item.errId);
                    if (errSpan) errSpan.style.display = 'none';
                };
                item.el.addEventListener('input', clearErr);
                item.el.addEventListener('change', clearErr);
            }
        });

        profileForm.addEventListener('submit', (e) => {
            // Solo validar la dirección si el editor de casillas está abierto
            if (addressActiveInput && addressActiveInput.value === '1') {
                clearAddressErrors();
                const missingFields = [];

                requiredAddressInputs.forEach(item => {
                    const val = item.el ? item.el.value.trim() : '';
                    if (!val) {
                        missingFields.push(item.name);
                        if (item.el) item.el.classList.add('is-invalid');
                        const errSpan = document.getElementById(item.errId);
                        if (errSpan) errSpan.style.display = 'block';
                    }
                });

                if (missingFields.length > 0) {
                    e.preventDefault();
                    e.stopPropagation();

                    // Hacer scroll al primer campo faltante
                    const firstInvalid = profileForm.querySelector('.is-invalid');
                    if (firstInvalid) {
                        firstInvalid.focus();
                        firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }

                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            title: 'Dirección incompleta',
                            html: `Para poder guardar la dirección de despacho debes completar todos los campos obligatorios:<br><br><strong>${missingFields.join(', ')}</strong>.`,
                            icon: 'warning',
                            confirmButtonColor: '#A65D37',
                            confirmButtonText: 'Entendido'
                        });
                    } else {
                        alert(`Para guardar la dirección de despacho debes completar: ${missingFields.join(', ')}.`);
                    }
                    return false;
                }
            }
        });
    }
});



//Mi contraseña
document.addEventListener('DOMContentLoaded', () => {
    const submitBtn = document.getElementById('submitBtn');
    const pwdErrorMsg = document.getElementById('pwdErrorMsg');

    const oldPassword = document.getElementById('id_old_password');
    const newPassword1 = document.getElementById('id_new_password1');
    const newPassword2 = document.getElementById('id_new_password2');

    // Referencias a los elementos de la lista de requisitos
    const reqLength = document.getElementById('req-length');
    const reqUpper = document.getElementById('req-upper');
    const reqSymbol = document.getElementById('req-symbol');

    if (oldPassword && newPassword1 && newPassword2) {
        const validateForm = () => {
            const valOld = oldPassword.value.trim();
            const valNew1 = newPassword1.value.trim();
            const valNew2 = newPassword2.value.trim();

            // Evaluaciones individuales
            const hasLength = valNew1.length >= 8;
            const hasUpper = /[A-Z]/.test(valNew1);
            const hasSymbol = /[\W\_]/.test(valNew1);
            const match = valNew1 === valNew2 && valNew2.length > 0;
            const allFilled = valOld.length > 0 && valNew1.length > 0 && valNew2.length > 0;

            // Actualizar colores de la lista de requisitos visualmente en tiempo real
            if (hasLength) { reqLength.classList.add('valid'); } else { reqLength.classList.remove('valid'); }
            if (hasUpper) { reqUpper.classList.add('valid'); } else { reqUpper.classList.remove('valid'); }
            if (hasSymbol) { reqSymbol.classList.add('valid'); } else { reqSymbol.classList.remove('valid'); }

            // Mostrar u ocultar mensaje de coincidencia
            if (valNew2.length > 0 && !match) {
                pwdErrorMsg.style.display = 'block';
            } else {
                pwdErrorMsg.style.display = 'none';
            }

            // Activar o desactivar el botón principal
            if (allFilled && hasLength && hasUpper && hasSymbol && match) {
                submitBtn.disabled = false;
            } else {
                submitBtn.disabled = true;
            }
        };

        oldPassword.addEventListener('input', validateForm);
        newPassword1.addEventListener('input', validateForm);
        newPassword2.addEventListener('input', validateForm);
    }
});


// Corfirmación de eliminación de cuenta con SweetAlert2
document.getElementById('delete-account-form').addEventListener('submit', function (event) {
    event.preventDefault();
    var deleteAccountForm = this;
    Swal.fire({
        title: "¿Estás seguro de Eliminar tu cuenta?",
        text: "Tu cuenta se conservará durante 30 días y podrás recuperarla iniciando sesión.",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#3085d6",
        cancelButtonColor: "#d33",
        confirmButtonText: "Sí, solicitar eliminación",
        cancelButtonText: "Cancelar"
    }).then(function (result) {
        if (result.isConfirmed) {
            Swal.fire({
                title: "Solicitud enviada",
                text: "Tu cuenta se eliminará en 30 días si no vuelves a iniciar sesión.",
                icon: "success"
            }).then(function () {
                deleteAccountForm.submit();
            });
        }
    });
});