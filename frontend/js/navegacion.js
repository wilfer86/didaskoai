// ==========================================
// navegacion.js - Didasko AI
// Manejo de navegación entre secciones
// ==========================================

// Ir a una sección específica
function irA(seccion) {
    // Ocultar todas las pantallas
    const pantallas = document.querySelectorAll('.pantalla');
    pantallas.forEach(p => p.classList.remove('activa'));

    // Mostrar la sección seleccionada
    const seccionActiva = document.getElementById(seccion);
    if (seccionActiva) {
        seccionActiva.classList.add('activa');
    }

    // Actualizar pestaña activa (solo en PC)
    const tabs = document.querySelectorAll('.tab-link');
    tabs.forEach(tab => tab.classList.remove('active'));

    // Buscar el tab que corresponde a esta sección
    tabs.forEach(tab => {
        const onclick = tab.getAttribute('onclick') || '';
        if (onclick.includes(`irA('${seccion}')`)) {
            tab.classList.add('active');
        }
    });

    // Scroll al inicio
    window.scrollTo({ top: 0, behavior: 'smooth' });

    if (CONFIG.DEBUG) console.log('📍 Navegando a:', seccion);
}

// Volver al inicio (bienvenida) - Solo móvil
function volverInicio() {
    const pantallas = document.querySelectorAll('.pantalla');
    pantallas.forEach(p => p.classList.remove('activa'));

    const bienvenida = document.getElementById('bienvenida');
    if (bienvenida) {
        bienvenida.classList.add('activa');
    }

    if (CONFIG.DEBUG) console.log('🏠 Volviendo al inicio');
}

// Selección de formato de imagen
function seleccionarFormato(formato) {
    const botones = document.querySelectorAll('.btn-formato');
    botones.forEach(btn => btn.classList.remove('active'));

    const btnSeleccionado = document.querySelector(`.btn-formato[data-formato="${formato}"]`);
    if (btnSeleccionado) {
        btnSeleccionado.classList.add('active');
    }

    // Guardar formato seleccionado globalmente
    window.formatoImagenSeleccionado = formato;

    if (CONFIG.DEBUG) console.log('🖼️ Formato seleccionado:', formato);
}

// Inicializar formato por defecto
window.formatoImagenSeleccionado = '1:1';

if (CONFIG.DEBUG) console.log('🧭 navegacion.js cargado');
