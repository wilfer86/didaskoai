// ==========================================
// chat.js - Didasko AI
// Manejo del chat con el búho
// ==========================================

// Enviar mensaje al backend
async function enviarMensaje() {
    const input = document.getElementById('chat-input');
    const mensajesDiv = document.getElementById('chat-mensajes');
    const mensaje = input.value.trim();

    if (!mensaje) return;

    // Mostrar mensaje del usuario
    agregarMensajeUsuario(mensaje);
    input.value = '';

    // Mostrar loader mientras carga
    const loaderId = mostrarLoader();

    try {
        const response = await fetch(apiUrl('/api/chat/mensaje'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                mensaje: mensaje,
                session_id: CONFIG.SESSION_ID
            })
        });

        const data = await response.json();

        // Quitar loader
        quitarLoader(loaderId);

        if (data.success) {
            agregarMensajeBuho(data.respuesta);

            // Contar tarea para publicidad
            if (typeof contarTareaPublicidad === 'function') {
                contarTareaPublicidad('chat');
            }
        } else {
            agregarMensajeError(data.message || 'Error al procesar mensaje');
        }
    } catch (error) {
        quitarLoader(loaderId);
        agregarMensajeError('No se pudo conectar con el servidor');
        if (CONFIG.DEBUG) console.error('Error chat:', error);
    }

    // Scroll al final
    scrollAlFinal();
}

// Agregar mensaje del usuario al chat
function agregarMensajeUsuario(mensaje) {
    const mensajesDiv = document.getElementById('chat-mensajes');
    const div = document.createElement('div');
    div.className = 'mensaje-chat mensaje-usuario';
    div.textContent = mensaje;
    mensajesDiv.appendChild(div);
    scrollAlFinal();
}

// Agregar mensaje del búho al chat
function agregarMensajeBuho(mensaje) {
    const mensajesDiv = document.getElementById('chat-mensajes');
    const div = document.createElement('div');
    div.className = 'mensaje-chat mensaje-buho';
    div.innerHTML = formatearTexto(mensaje);
    mensajesDiv.appendChild(div);
    scrollAlFinal();
}

// Agregar mensaje de error
function agregarMensajeError(mensaje) {
    const mensajesDiv = document.getElementById('chat-mensajes');
    const div = document.createElement('div');
    div.className = 'mensaje-error';
    div.innerHTML = `❌ ${mensaje}`;
    mensajesDiv.appendChild(div);
    scrollAlFinal();
}

// Mostrar loader mientras espera respuesta
function mostrarLoader() {
    const mensajesDiv = document.getElementById('chat-mensajes');
    const id = 'loader-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'mensaje-chat mensaje-buho';
    div.innerHTML = '<span class="loader"></span> 🦉 Pensando...';
    mensajesDiv.appendChild(div);
    scrollAlFinal();
    return id;
}

// Quitar loader
function quitarLoader(id) {
    const loader = document.getElementById(id);
    if (loader) loader.remove();
}

// Formatear texto (convierte saltos de línea y **bold**)
function formatearTexto(texto) {
    return texto
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
}

// Scroll automático al final
function scrollAlFinal() {
    const mensajesDiv = document.getElementById('chat-mensajes');
    if (mensajesDiv) {
        mensajesDiv.scrollTop = mensajesDiv.scrollHeight;
    }
}

// Enviar mensaje con tecla Enter
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('chat-input');
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                enviarMensaje();
            }
        });
    }
});

if (CONFIG.DEBUG) console.log('💬 chat.js cargado');
