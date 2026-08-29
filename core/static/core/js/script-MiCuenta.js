// =========================
// ACORDEÓN MIS COMPRAS (Página Mi Cuenta)
// =========================
document.addEventListener('DOMContentLoaded', () => {
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
// VALIDACIÓN DE CAMBIOS EN MI PERFIL
// =========================
document.addEventListener('DOMContentLoaded', () => {
    const profileForm = document.querySelector('.profile-form');

    // Solo ejecutamos esto si estamos en la página de Mi Perfil
    if (profileForm) {
        const saveButton = profileForm.querySelector('button[type="submit"]');
        // Ignoramos el token CSRF oculto de Django
        const inputs = profileForm.querySelectorAll('input:not([name="csrfmiddlewaretoken"]), select');

        // 1. Guardar los valores iniciales al cargar la página
        const initialValues = {};
        inputs.forEach(input => {
            initialValues[input.name] = input.value;
        });

        // 2. Función que compara los valores actuales con los iniciales
        const checkChanges = () => {
            let hasChanged = false;
            inputs.forEach(input => {
                if (input.value !== initialValues[input.name]) {
                    hasChanged = true;
                }
            });

            // Habilita el botón si hay cambios, lo deshabilita si está igual
            saveButton.disabled = !hasChanged;
        };

        // 3. Ejecutar la validación inicial para deshabilitarlo al entrar
        checkChanges();

        // 4. Escuchar cada vez que el usuario escribe o cambia una opción
        inputs.forEach(input => {
            input.addEventListener('input', checkChanges);
            input.addEventListener('change', checkChanges);
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