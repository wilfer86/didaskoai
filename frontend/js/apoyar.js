// ==========================================
// apoyar.js - Didasko AI
// Manejo de la sección Apoyar Proyecto
// Copia al portapapeles al tocar
// ==========================================

// Inicializar cuando cargue el DOM
document.addEventListener('DOMContentLoaded', function() {
    inicializarBotonesApoyo();
});

// Configurar los botones de pago
function inicializarBotonesApoyo() {
    const tarjetasPago = document.querySelectorAll('.pago-card');

    tarjetasPago.forEach(tarjeta => {
        // Hacer clickeable toda la tarjeta
        tarjeta.style.cursor = 'pointer';

        tarjeta.addEventListener('click', function() {
            // Obtener el texto del <p> (el dato a copiar)
            const parrafos = tarjeta.querySelectorAll('p');
            let datoACopiar = '';

            parrafos.forEach(p => {
                const texto = p.textContent.trim();
                // Buscar el que parece un correo o número
                if (texto.includes('@') || /^\d+$/.test(texto)) {
                    datoACopiar = texto;
                }
            });

            if (datoACopiar) {
                copiarAlPortapapeles(datoACopiar, tarjeta);
            }
        });
    });

    if (CONFIG.DEBUG) {
        console.log(`💰 Botones de apoyo inicializados: ${tarjetasPago.length}`);
    }
}

// Copiar texto al portapapeles
async function copiarAlPortapapeles(texto, tarjeta) {
    try {
        // Método moderno (funciona en la mayoría de navegadores)
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(texto);
        } else {
            // Método alternativo para navegadores viejos
            copiarAlternativo(texto);
        }

        mostrarConfirmacionCopia(tarjeta, texto);

        if (CONFIG.DEBUG) console.log(`📋 Copiado: ${texto}`);
    } catch (error) {
        if (CONFIG.DEBUG) console.error('Error al copiar:', error);
        mostrarErrorCopia(tarjeta);
    }
}

// Método alternativo de copia (para navegadores viejos)
function copiarAlternativo(texto) {
    const textArea = document.createElement('textarea');
    textArea.value = texto;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
}

// Mostrar confirmación visual de "¡Copiado!"
function mostrarConfirmacionCopia(tarjeta, texto) {
    // Verificar si ya hay una confirmación
    const existente = tarjeta.querySelector('.confirmacion-copia');
    if (existente) existente.remove();

    // Crear elemento de confirmación
    const confirmacion = document.createElement('div');
    confirmacion.className = 'confirmacion-copia';
    confirmacion.innerHTML = `✅ ¡Copiado!<br><small>${texto}</small>`;
    tarjeta.appendChild(confirmacion);

    // Efecto de animación en la tarjeta
    tarjeta.classList.add('tarjeta-copiada');

    // Quitar después de 2 segundos
    setTimeout(() => {
        confirmacion.remove();
        tarjeta.classList.remove('tarjeta-copiada');
    }, 2000);
}

// Mostrar error de copia
function mostrarErrorCopia(tarjeta) {
    const error = document.createElement('div');
    error.className = 'confirmacion-copia error';
    error.innerHTML = '❌ Copia manualmente';
    tarjeta.appendChild(error);

    setTimeout(() => {
        error.remove();
    }, 2000);
}

if (CONFIG.DEBUG) console.log('💰 apoyar.js cargado');
