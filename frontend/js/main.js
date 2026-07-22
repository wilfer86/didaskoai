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
        // Activar el tab de chat
        activarTab('chat');
    }
}

// Activar visualmente la pestaña seleccionada (PC)
function activarTab(seccion) {
    const tabs = document.querySelectorAll('.tab-link');
    tabs.forEach(tab => tab.classList.remove('active'));

    // Buscar el tab correcto
    tabs.forEach(tab => {
        if (tab.getAttribute('onclick') && tab.getAttribute('onclick').includes(`'${seccion}'`)) {
            tab.classList.add('active');
        }
    });
}

// Detectar cambios de tamaño de pantalla (ej: rotar celular)
window.addEventListener('resize', () => {
    // Si cambia entre móvil/PC drásticamente, reiniciar vista
    const pantallaActiva = document.querySelector('.pantalla.activa');
    const idActivo = pantallaActiva ? pantallaActiva.id : null;

    if (esMovil() && idActivo === 'chat' && !pantallaActiva.dataset.usuarioEntró) {
        // Si cambia a móvil y estaba en chat sin haber entrado manualmente, volver a bienvenida
        mostrarPantalla('bienvenida');
    }
});

// Iniciar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', iniciarApp);
} else {
    iniciarApp();
}