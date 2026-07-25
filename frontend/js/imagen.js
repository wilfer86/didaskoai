// ==========================================
// imagen.js - Didasko AI
// Crear imágenes con sistema dual (HF + Pollinations)
// ==========================================

// Formato seleccionado por defecto
let formatoImagenActual = '1:1';

// Actualizar formato cuando el usuario selecciona
function actualizarFormatoImagen(formato) {
    formatoImagenActual = formato;
    if (CONFIG.DEBUG) console.log('🖼️ Formato imagen:', formato);
}

// Función principal: crear imagen
async function crearImagen() {
    const input = document.getElementById('imagen-input');
    const resultado = document.getElementById('imagen-resultado');
    const prompt = input.value.trim();

    if (!prompt) {
        mostrarErrorImagen('Escribe una descripción de la imagen');
        return;
    }

    // Obtener formato del botón activo
    const botonActivo = document.querySelector('.btn-formato.active');
    const formato = botonActivo ? botonActivo.dataset.formato : '1:1';

    // Mostrar loader
    resultado.innerHTML = `
        <div class="loader-imagen">
            <span class="loader"></span>
            <p>🎨 Generando tu imagen...</p>
            <p class="texto-espera">Esto puede tomar 10-30 segundos</p>
        </div>
    `;

    input.value = '';

    try {
        const response = await fetch(apiUrl('/api/imagen/crear'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: prompt,
                formato: formato
            })
        });

        const data = await response.json();

        if (data.success && data.imagen_url) {
            mostrarImagen(data.imagen_url, prompt, formato, data.proveedor);

            // Contar tarea para publicidad
            if (typeof contarTareaPublicidad === 'function') {
                contarTareaPublicidad('imagen');
            }
        } else {
            mostrarErrorImagen(data.message || 'Error al crear imagen');
        }
    } catch (error) {
        mostrarErrorImagen('No se pudo conectar con el servidor');
        if (CONFIG.DEBUG) console.error('Error imagen:', error);
    }
}

// Mostrar imagen generada
function mostrarImagen(url, prompt, formato, proveedor) {
    const resultado = document.getElementById('imagen-resultado');

    // Clase CSS según formato
    const claseFormato = `formato-${formato.replace(':', '-')}`;

    resultado.innerHTML = `
        <div class="imagen-generada">
            <img src="${url}" alt="Imagen generada" class="imagen-resultado-img ${claseFormato}">
            <div class="imagen-info">
                <p class="prompt-usado">📝 "${prompt}"</p>
                <p class="formato-usado">🖼️ Formato: ${formato} | 🤖 ${proveedor || 'IA'}</p>
                <div class="imagen-acciones">
                    <a href="${url}" download="didasko-imagen.png" target="_blank" class="btn-descargar">
                        📥 Descargar
                    </a>
                    <button onclick="crearOtraImagen()" class="btn-otra">
                        🔄 Crear otra
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Mostrar error
function mostrarErrorImagen(mensaje) {
    const resultado = document.getElementById('imagen-resultado');
    resultado.innerHTML = `
        <div class="mensaje-error">
            ❌ ${mensaje}
        </div>
    `;
}

// Limpiar y volver a intentar
function crearOtraImagen() {
    const resultado = document.getElementById('imagen-resultado');
    resultado.innerHTML = '';
    document.getElementById('imagen-input').focus();
}

// Enviar con Enter
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('imagen-input');
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                crearImagen();
            }
        });
    }
});

if (CONFIG.DEBUG) console.log('🎨 imagen.js cargado');
