// ==========================================
// publicidad.js - Didasko AI
// Sistema de anuncios cada 3 tareas
// ==========================================

// Clave para guardar contador en el navegador
const STORAGE_KEY = 'didasko_contador_tareas';

// Obtener contador actual (0 si no existe)
function obtenerContadorTareas() {
    const valor = localStorage.getItem(STORAGE_KEY);
    return valor ? parseInt(valor, 10) : 0;
}

// Guardar contador
function guardarContadorTareas(valor) {
    localStorage.setItem(STORAGE_KEY, valor.toString());
}

// Función principal: se llama después de cada tarea completada
function contarTareaPublicidad(tipoTarea) {
    let contador = obtenerContadorTareas();
    contador++;
    guardarContadorTareas(contador);

    if (CONFIG.DEBUG) {
        console.log(`📊 Tarea completada: ${tipoTarea}`);
        console.log(`📊 Total tareas: ${contador}`);
    }

    // Cada X tareas mostrar publicidad
    const frecuencia = CONFIG.AD_FREQUENCY || 3;

    if (contador % frecuencia === 0) {
        setTimeout(() => {
            mostrarPublicidad(tipoTarea);
        }, 800);
    }
}

// Mostrar anuncio publicitario
function mostrarPublicidad(tipoTarea) {
    if (CONFIG.DEBUG) console.log('📢 Mostrando publicidad');

    // Determinar dónde insertar el anuncio según el tipo de tarea
    let contenedor = null;

    switch (tipoTarea) {
        case 'chat':
            contenedor = document.getElementById('chat-mensajes');
            break;
        case 'imagen':
            contenedor = document.getElementById('imagen-resultado');
            break;
        case 'vision':
            contenedor = document.getElementById('vision-resultado');
            break;
        case 'video':
            contenedor = document.getElementById('video-resultado');
            break;
    }

    if (!contenedor) return;

    // Crear el div del anuncio
    const anuncio = document.createElement('div');
    anuncio.className = 'anuncio-publicidad ad-anim';
    anuncio.onclick = abrirWhatsAppPublicidad;
    anuncio.innerHTML = `
        <div class="anuncio-contenido">
            <span class="anuncio-icono">📢</span>
            <div class="anuncio-texto">
                <p class="anuncio-titulo">¿Quieres publicidad aquí?</p>
                <p class="anuncio-numero">Contáctanos: +57 317 154 7065</p>
            </div>
            <span class="anuncio-flecha">👆 Toca aquí</span>
        </div>
    `;

    contenedor.appendChild(anuncio);

    // Scroll para asegurar que se vea
    if (tipoTarea === 'chat') {
        anuncio.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

// Abrir WhatsApp cuando toquen el anuncio
function abrirWhatsAppPublicidad() {
    const numero = CONFIG.AD_WHATSAPP || '573171547065';
    const mensaje = encodeURIComponent('Hola, vi tu anuncio en Didasko AI y me interesa contratar publicidad.');
    const url = `https://wa.me/${numero}?text=${mensaje}`;
    window.open(url, '_blank');

    if (CONFIG.DEBUG) console.log('📱 Abriendo WhatsApp:', url);
}

// Reiniciar contador (útil si se quiere ofrecer opción "restablecer")
function reiniciarContadorPublicidad() {
    localStorage.removeItem(STORAGE_KEY);
    if (CONFIG.DEBUG) console.log('🔄 Contador de publicidad reiniciado');
}

if (CONFIG.DEBUG) {
    const contadorActual = obtenerContadorTareas();
    console.log(`📢 publicidad.js cargado - Tareas actuales: ${contadorActual}`);
}
