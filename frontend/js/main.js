// ==========================================
// main.js - Didasko AI
// Inicialización de la aplicación
// ==========================================

// Detectar si es móvil o PC
function esMovil() {
    return window.innerWidth <= 768;
}

// Ocultar TODAS las pantallas
function ocultarTodasLasPantallas() {
    const pantallas = document.querySelectorAll('.pantalla');
    pantallas.forEach(p => p.classList.remove('activa'));
}

// Mostrar solo UNA pantalla
function mostrarPantalla(id) {
    ocultarTodasLasPantallas();
    const pantalla = document.getElementById(id);
    if (pantalla) {
        pantalla.classList.add('activa');
        window.scrollTo(0, 0);
        if (CONFIG.DEBUG) console.log('📺 Mostrando pantalla:', id);
    } else {
        console.warn('⚠️ Pantalla no encontrada:', id);
    }
}

// Inicializar la app
function iniciarApp() {
    if (CONFIG.DEBUG) {
        console.log('🚀 Iniciando Didasko AI...');
        console.log('📱 Modo:', esMovil() ? 'Móvil (App)' : 'PC (Web)');
        console.log('📐 Ancho ventana:', window.innerWidth + 'px');
    }

    // Ocultar todo primero
    ocultarTodasLasPantallas();

    // Decidir pantalla inicial
    if (esMovil()) {
        // 📱 MÓVIL: Muestra bienvenida
        mostrarPantalla('bienvenida');
    } else {
        // 💻 PC: Muestra chat directamente
        mostrarPantalla('chat');
        activarTab('chat');
    }
}

// Activar visualmente la pestaña seleccionada (PC)
function activarTab(seccion) {
    const tabs = document.querySelectorAll('.tab-link');
    tabs.forEach(tab => tab.classList.remove('active'));

    tabs.forEach(tab => {
        if (tab.getAttribute('onclick') && tab.getAttribute('onclick').includes(`'${seccion}'`)) {
            tab.classList.add('active');
        }
    });
}

// Re-inicializar si cambia el tamaño (rotación o resize)
// Re-inicializar SOLO si cambia entre móvil/PC (no en cada resize del teclado)
let anchoAnterior = window.innerWidth;
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        const anchoActual = window.innerWidth;
        const erayaMovil = anchoAnterior <= 768;
        const esAhoraMovil = anchoActual <= 768;

        // Solo re-inicializar si cambió de móvil a PC o viceversa
        if (erayaMovil !== esAhoraMovil) {
            if (CONFIG.DEBUG) console.log('🔄 Cambio de modo:', anchoActual + 'px');
            iniciarApp();
        }
        anchoAnterior = anchoActual;
    }, 300);
});

// Iniciar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciarApp);
} else {
    iniciarApp();
}

// ===================================
// Registrar Service Worker (PWA)
// ===================================
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/pwa/service-worker.js')
            .then(registration => {
                if (CONFIG.DEBUG) {
                    console.log('✅ Service Worker registrado:', registration.scope);
                }
            })
            .catch(error => {
                if (CONFIG.DEBUG) {
                    console.error('❌ Error registrando Service Worker:', error);
                }
            });
    });
}
