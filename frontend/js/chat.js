// ==========================================
// chat.js - Didasko AI V3.0
// Chat con historial persistente
// ==========================================

let historialCargado = false;

// ==========================================
// 🔄 Cargar historial visual al abrir chat
// ==========================================
async function cargarHistorialVisual() {
    if (historialCargado) return;

    const mensajesDiv = document.getElementById('chat-mensajes');
    if (!mensajesDiv) return;

    try {
        const response = await fetch('/api/chat/historial?limite=20', {
            credentials: 'include'
        });
        const data = await response.json();

        if (data.success && data.historial && data.historial.length > 0) {
            // Ordenar de más antiguo a más reciente
            const historial = data.historial.reverse();

            historial.forEach(chat => {
                if (chat.seccion === 'chat') {
                    agregarMensajeUsuario(chat.mensaje_usuario, false);
                    agregarMensajeBuho(chat.respuesta_ia, false);
                }
            });

            // Mensaje de bienvenida al retomar
            if (historial.length > 0) {
                const divInfo = document.createElement('div');
                divInfo.className = 'mensaje-info-historial';
                divInfo.style.cssText = 'text-align:center; padding:10px; margin:10px 0; background:rgba(212,175,55,0.1); border-radius:8px; color:#d4af37; font-size:13px;';
                divInfo.innerHTML = '🦉 <strong>Historial recuperado</strong> — Continúa donde lo dejaste';
                mensajesDiv.appendChild(divInfo);
            }

            scrollAlFinal();
        }

        historialCargado = true;
    } catch (error) {
        if (CONFIG.DEBUG) console.warn('No se pudo cargar historial:', error);
    }
}

// ==========================================
// 📤 Enviar mensaje al backend
// ==========================================
async function enviarMensaje() {
    const input = document.getElementById('chat-input');
    const mensaje = input.value.trim();

    if (!mensaje) return;

    agregarMensajeUsuario(mensaje);
    input.value = '';

    const loaderId = mostrarLoader();

    try {
        const response = await fetch('/api/chat/mensaje', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                mensaje: mensaje,
                session_id: obtenerSessionUsuario()
            })
        });

        const data = await response.json();
        quitarLoader(loaderId);

        if (data.success) {
            agregarMensajeBuho(data.respuesta);

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

    scrollAlFinal();
}

// ==========================================
// 🔑 Obtener session_id ligado al usuario
// ==========================================
function obtenerSessionUsuario() {
    const usuarioData = localStorage.getItem('didasko_usuario');
    if (usuarioData) {
        try {
            const usuario = JSON.parse(usuarioData);
            return 'user_' + usuario.id;
        } catch (e) {
            return 'default';
        }
    }
    return 'default';
}

// ==========================================
// 💬 Agregar mensajes
// ==========================================
function agregarMensajeUsuario(mensaje, scroll = true) {
    const mensajesDiv = document.getElementById('chat-mensajes');
    const div = document.createElement('div');
    div.className = 'mensaje-chat mensaje-usuario';
    div.textContent = mensaje;
    mensajesDiv.appendChild(div);
    if (scroll) scrollAlFinal();
}

function agregarMensajeBuho(mensaje, scroll = true) {
    const mensajesDiv = document.getElementById('chat-mensajes');
    const div = document.createElement('div');
    div.className = 'mensaje-chat mensaje-buho';
    div.innerHTML = formatearTexto(mensaje);
    mensajesDiv.appendChild(div);
    if (scroll) scrollAlFinal();
    renderizarMatematicas(div);
}

function agregarMensajeError(mensaje) {
    const mensajesDiv = document.getElementById('chat-mensajes');
    const div = document.createElement('div');
    div.className = 'mensaje-error';
    div.innerHTML = `❌ ${mensaje}`;
    mensajesDiv.appendChild(div);
    scrollAlFinal();
}

// ==========================================
// ⏳ Loader
// ==========================================
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

function quitarLoader(id) {
    const loader = document.getElementById(id);
    if (loader) loader.remove();
}

// ==========================================
// 🧮 Normalizar LaTeX
// ==========================================
function normalizarLatex(texto) {
    texto = texto.replace(/\(\((.+?)\)\)/g, '$$$1$$');
    texto = texto.replace(/\((\\[a-zA-Z]+.*?)\)/g, '$$$1$$');
    texto = texto.replace(/\\\((.+?)\\\)/g, '$$$1$$');
    texto = texto.replace(/\\\[(.+?)\\\]/g, '$$$$$1$$$$');
    return texto;
}

// ==========================================
// 📝 Formatear Markdown
// ==========================================
function formatearTexto(texto) {
    texto = normalizarLatex(texto);

    if (typeof marked !== 'undefined') {
        marked.setOptions({ breaks: true, gfm: true });
        return marked.parse(texto);
    } else {
        return texto
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }
}

// ==========================================
// 🧮 Renderizar MathJax
// ==========================================
function renderizarMatematicas(elemento) {
    if (window.MathJax && window.MathJax.typesetPromise) {
        window.MathJax.typesetPromise([elemento]).catch(function(err) {
            if (CONFIG.DEBUG) console.error('MathJax error:', err);
        });
    }
}

// ==========================================
// 📜 Scroll al final
// ==========================================
function scrollAlFinal() {
    const mensajesDiv = document.getElementById('chat-mensajes');
    if (mensajesDiv) {
        mensajesDiv.scrollTop = mensajesDiv.scrollHeight;
    }
}

// ==========================================
// 🚀 Al cargar la página
// ==========================================
document.addEventListener('DOMContentLoaded', function() {
    // Enter para enviar
    const input = document.getElementById('chat-input');
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                enviarMensaje();
            }
        });
    }

    // Cargar historial visual al inicio
    setTimeout(cargarHistorialVisual, 1000);
});

if (CONFIG.DEBUG) console.log('💬 chat.js V3.0 cargado');
