// ==========================================
// video.js - Didasko AI
// Sistema de "video" con Pollinations (imagen cinematográfica 9:16)
// Nota: Cuando se tenga API de Sora/Meta AI, se puede activar video real
// ==========================================

let videoStartTime = null;

// Función principal: crear video (imagen cinematográfica 9:16)
async function crearVideo() {
    const input = document.getElementById('video-input');
    const resultado = document.getElementById('video-resultado');
    const prompt = input.value.trim();

    if (!prompt) {
        mostrarErrorVideo('Escribe una descripción del video');
        return;
    }

    videoStartTime = Date.now();

    // Mostrar loader
    resultado.innerHTML = `
        <div class="video-generando">
            <div class="loader"></div>
            <p class="video-mensaje">🎬 Generando escena cinematográfica...</p>
            <p class="video-info">Esto puede tomar 10-20 segundos</p>
        </div>
    `;

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

        if (data.success && data.video_url) {
            mostrarVideo(data.video_url, prompt);

            // Contar tarea para publicidad
            if (typeof contarTareaPublicidad === 'function') {
                contarTareaPublicidad('video');
            }
        } else {
            mostrarErrorVideo(data.message || 'Error al crear video');
        }
    } catch (error) {
        mostrarErrorVideo('No se pudo conectar con el servidor');
        if (CONFIG.DEBUG) console.error('Error video:', error);
    }
}

// Mostrar "video" generado (imagen cinematográfica 9:16)
function mostrarVideo(url, prompt) {
    const resultado = document.getElementById('video-resultado');
    resultado.innerHTML = `
        <div class="video-generado">
            <div class="video-banner-info">
                🎬 <strong>Escena Cinematográfica 9:16</strong>
                <p class="video-banner-nota">💡 Generación de video real próximamente</p>
            </div>
            <img src="${url}" alt="Escena generada" class="video-resultado-video">
            <div class="video-info-final">
                <p class="prompt-usado">📝 "${prompt}"</p>
                <p class="formato-usado">📱 Formato: (9:16) | 🤖 Pollinations AI</p>
                <div class="video-acciones">
                    <a href="${url}" download="didasko-escena.png" target="_blank" class="btn-descargar">
                        📥 Descargar
                    </a>
                    <button onclick="crearOtroVideo()" class="btn-otra">
                        🎬 Crear otra
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Mostrar error
function mostrarErrorVideo(mensaje) {
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
