// ==========================================
// video.js - Didasko AI
// Crear videos con SiliconFlow (CogVideoX)
// Formato fijo 9:16
// ==========================================

let videoPollingInterval = null;
let videoStartTime = null;

// Función principal: crear video
async function crearVideo() {
    const input = document.getElementById('video-input');
    const resultado = document.getElementById('video-resultado');
    const prompt = input.value.trim();

    if (!prompt) {
        mostrarErrorVideo('Escribe una descripción del video');
        return;
    }

    // Detener polling anterior si existe
    detenerPolling();

    // Mostrar loader inicial
    videoStartTime = Date.now();
    mostrarLoaderVideo(0, 'Enviando solicitud...');

    input.value = '';

    try {
        const response = await fetch(apiUrl('/api/video/crear'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: prompt
            })
        });

        const data = await response.json();

        if (data.success && data.request_id) {
            // Iniciar polling para consultar estado
            iniciarPolling(data.request_id, prompt);
        } else {
            mostrarErrorVideo(data.message || 'Error al crear video');
        }
    } catch (error) {
        mostrarErrorVideo('No se pudo conectar con el servidor');
        if (CONFIG.DEBUG) console.error('Error video:', error);
    }
}

// Iniciar consulta periódica del estado
function iniciarPolling(requestId, prompt) {
    if (CONFIG.DEBUG) console.log('🎬 Iniciando polling para:', requestId);

    // Consultar inmediatamente
    consultarEstadoVideo(requestId, prompt);

    // Y cada 10 segundos
    videoPollingInterval = setInterval(() => {
        consultarEstadoVideo(requestId, prompt);
    }, CONFIG.VIDEO_POLL_INTERVAL || 10000);
}

// Detener polling
function detenerPolling() {
    if (videoPollingInterval) {
        clearInterval(videoPollingInterval);
        videoPollingInterval = null;
    }
}

// Consultar si el video está listo
async function consultarEstadoVideo(requestId, prompt) {
    try {
        const response = await fetch(apiUrl('/api/video/estado'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                request_id: requestId
            })
        });

        const data = await response.json();

        // Calcular tiempo transcurrido
        const tiempoTranscurrido = Math.floor((Date.now() - videoStartTime) / 1000);

        if (data.estado === 'listo' && data.video_url) {
            detenerPolling();
            mostrarVideo(data.video_url, prompt);

            // Contar tarea para publicidad
            if (typeof contarTareaPublicidad === 'function') {
                contarTareaPublicidad('video');
            }
        } 
        else if (data.estado === 'procesando') {
            mostrarLoaderVideo(tiempoTranscurrido, '🎬 Generando video...');
        } 
        else if (data.estado === 'fallido') {
            detenerPolling();
            mostrarErrorVideo('La generación del video falló. Intenta de nuevo.');
        }
        else {
            // Estado desconocido, seguir intentando
            mostrarLoaderVideo(tiempoTranscurrido, 'Esperando respuesta...');
        }

        // Timeout después de 5 minutos
        if (tiempoTranscurrido > 300) {
            detenerPolling();
            mostrarErrorVideo('El video está tardando demasiado. Intenta de nuevo.');
        }

    } catch (error) {
        if (CONFIG.DEBUG) console.error('Error consultando video:', error);
    }
}

// Mostrar loader con progreso
function mostrarLoaderVideo(segundos, mensaje) {
    const resultado = document.getElementById('video-resultado');
    const minutos = Math.floor(segundos / 60);
    const segs = segundos % 60;
    const tiempoFormato = `${minutos}:${segs.toString().padStart(2, '0')}`;

    resultado.innerHTML = `
        <div class="video-generando">
            <div class="loader"></div>
            <p class="video-mensaje">${mensaje}</p>
            <p class="video-tiempo">⏱️ Tiempo: ${tiempoFormato}</p>
            <p class="video-info">Los videos tardan entre 1 y 3 minutos.<br>Por favor no cierres la ventana.</p>
            <div class="barra-progreso">
                <div class="barra-progreso-fill" style="width: ${Math.min((segundos / 180) * 100, 95)}%"></div>
            </div>
        </div>
    `;
}

// Mostrar video generado
function mostrarVideo(url, prompt) {
    const resultado = document.getElementById('video-resultado');
    resultado.innerHTML = `
        <div class="video-generado">
            <video controls autoplay loop class="video-resultado-video">
                <source src="${url}" type="video/mp4">
                Tu navegador no soporta videos.
            </video>
            <div class="video-info-final">
                <p class="prompt-usado">📝 "${prompt}"</p>
                <p class="formato-usado">📱 Formato: 9:16 (Vertical)</p>
                <div class="video-acciones">
                    <a href="${url}" download="didasko-video.mp4" class="btn-descargar">
                        ⬇️ Descargar
                    </a>
                    <button onclick="crearOtroVideo()" class="btn-otra">
                        🔄 Crear otro
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Mostrar error
function mostrarErrorVideo(mensaje) {
    detenerPolling();
    const resultado = document.getElementById('video-resultado');
    resultado.innerHTML = `
        <div class="mensaje-error">
            ❌ ${mensaje}
        </div>
    `;
}

// Limpiar y volver a intentar
function crearOtroVideo() {
    const resultado = document.getElementById('video-resultado');
    resultado.innerHTML = '';
    document.getElementById('video-input').focus();
}

// Enviar con Enter
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('video-input');
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                crearVideo();
            }
        });
    }
});

if (CONFIG.DEBUG) console.log('🎬 video.js cargado');
