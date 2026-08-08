// ==========================================
// vision.js - Didasko AI V3.0
// Analizar fotos + Historial persistente
// ==========================================

let imagenSeleccionada = null;
let historialVisionCargado = false;

// ==========================================
// Inicialización
// ==========================================
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('vision-file');
    if (fileInput) {
        fileInput.addEventListener('change', manejarSeleccionArchivo);
    }

    const camaraInput = document.getElementById('vision-camara');
    if (camaraInput) {
        camaraInput.addEventListener('change', manejarSeleccionArchivo);
    }

    const inputTexto = document.getElementById('vision-input');
    if (inputTexto) {
        inputTexto.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                analizarImagen();
            }
        });
    }

    // Cargar historial al inicio
    setTimeout(cargarHistorialVision, 1500);
});

// ==========================================
// 🔄 Cargar historial de análisis
// ==========================================
async function cargarHistorialVision() {
    if (historialVisionCargado) return;

    try {
        const response = await fetch('/api/vision/historial?limite=12', {
            credentials: 'include'
        });
        const data = await response.json();

        if (data.success && data.analisis && data.analisis.length > 0) {
            mostrarHistorialVision(data.analisis);
        }

        historialVisionCargado = true;
    } catch (error) {
        if (CONFIG.DEBUG) console.warn('No se cargó historial vision:', error);
    }
}

// ==========================================
// 📸 Mostrar historial de análisis previos
// ==========================================
function mostrarHistorialVision(analisis) {
    const resultado = document.getElementById('vision-resultado');
    if (!resultado || resultado.innerHTML.trim() !== '') return;

    const htmlHistorial = `
        <div class="historial-vision">
            <h3 class="galeria-titulo">🔍 Tus análisis anteriores</h3>
            <div class="galeria-grid">
                ${analisis.map(item => `
                    <div class="galeria-item vision-item" onclick="verAnalisisCompleto('${item.id}', ${JSON.stringify(item.imagen_url || '').replace(/"/g, '&quot;')}, ${JSON.stringify(item.prompt).replace(/"/g, '&quot;')}, ${JSON.stringify(item.respuesta).replace(/"/g, '&quot;')})">
                        ${item.imagen_url ? `<img src="${item.imagen_url}" alt="Análisis" loading="lazy">` : `<div class="vision-sin-imagen">🔍</div>`}
                        <div class="galeria-info">
                            <span class="galeria-tipo">🔍</span>
                            <p class="galeria-prompt">${item.prompt.substring(0, 40)}${item.prompt.length > 40 ? '...' : ''}</p>
                        </div>
                    </div>
                `).join('')}
            </div>
            <p class="galeria-hint">👆 Toca un análisis para verlo completo</p>
        </div>
    `;

    resultado.innerHTML = htmlHistorial;
}

// ==========================================
// 🔍 Ver análisis completo desde historial
// ==========================================
function verAnalisisCompleto(id, imagenUrl, prompt, respuesta) {
    const resultado = document.getElementById('vision-resultado');

    resultado.innerHTML = `
        <div class="vision-resultado-completo">
            ${imagenUrl ? `<img src="${imagenUrl}" alt="Imagen analizada" class="preview-img">` : ''}
            <div class="analisis-buho">
                <h3>🦉 Análisis del búho:</h3>
                <p class="prompt-analizado">📝 Pregunta: "${prompt}"</p>
                <div class="analisis-texto">${formatearTextoVision(respuesta)}</div>
            </div>
            <div class="imagen-acciones">
                <button onclick="volverAHistorialVision()" class="btn-otra">
                    📚 Ver historial
                </button>
                <button onclick="analizarOtraFoto()" class="btn-otra">
                    📸 Analizar otra foto
                </button>
                <button onclick="eliminarAnalisisHistorial('${id}')" class="btn-otra" style="background: linear-gradient(135deg, #e74c3c, #c0392b); color: white;">
                    🗑️ Eliminar
                </button>
            </div>
        </div>
    `;

    renderizarMatematicasVision(resultado);
}

// ==========================================
// 🗑️ Eliminar análisis del historial
// ==========================================
async function eliminarAnalisisHistorial(analisisId) {
    if (!confirm('🤔 ¿Eliminar este análisis del historial?')) return;

    try {
        await fetch(`/api/vision/eliminar/${analisisId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        historialVisionCargado = false;
        volverAHistorialVision();
    } catch (error) {
        if (CONFIG.DEBUG) console.error('Error eliminando:', error);
    }
}

// ==========================================
// 📚 Volver al historial
// ==========================================
function volverAHistorialVision() {
    historialVisionCargado = false;
    imagenSeleccionada = null;
    const resultado = document.getElementById('vision-resultado');
    resultado.innerHTML = '';
    cargarHistorialVision();
}

// ==========================================
// Manejar cuando eligen un archivo
// ==========================================
function manejarSeleccionArchivo(evento) {
    const archivo = evento.target.files[0];
    if (!archivo) return;

    if (!archivo.type.startsWith('image/')) {
        mostrarErrorVision('El archivo debe ser una imagen');
        return;
    }

    if (archivo.size > 10 * 1024 * 1024) {
        mostrarErrorVision('La imagen es muy grande (máximo 10 MB)');
        return;
    }

    imagenSeleccionada = archivo;
    mostrarPreviewImagen(archivo);
}

// ==========================================
// Mostrar preview de imagen seleccionada
// ==========================================
function mostrarPreviewImagen(archivo) {
    const resultado = document.getElementById('vision-resultado');
    const reader = new FileReader();

    reader.onload = function(e) {
        resultado.innerHTML = `
            <div class="vision-preview">
                <img src="${e.target.result}" alt="Imagen a analizar" class="preview-img">
                <p class="preview-nombre">📎 ${archivo.name}</p>
                <p class="preview-hint">👇 Ahora escribe qué quieres saber y presiona ➤</p>
            </div>
        `;
    };

    reader.readAsDataURL(archivo);
}

// ==========================================
// Analizar imagen
// ==========================================
async function analizarImagen() {
    const input = document.getElementById('vision-input');
    const resultado = document.getElementById('vision-resultado');
    const prompt = input.value.trim();

    if (!imagenSeleccionada) {
        mostrarErrorVision('Primero selecciona una imagen con el botón 📸');
        return;
    }

    const reader = new FileReader();
    reader.onload = async function(e) {
        const imagenBase64 = e.target.result;

        resultado.innerHTML = `
            <div class="vision-analizando">
                <img src="${imagenBase64}" alt="Analizando" class="preview-img">
                <div class="loader-vision">
                    <span class="loader"></span>
                    <p>🔍 Analizando imagen...</p>
                </div>
            </div>
        `;

        input.value = '';

        try {
            const response = await fetch('/api/vision/analizar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    imagen_base64: imagenBase64,
                    prompt: prompt || 'Analiza esta imagen y ayúdame con lo que ves. Explica paso a paso.'
                })
            });

            const data = await response.json();

            if (data.success) {
                mostrarAnalisis(imagenBase64, data.respuesta);
                historialVisionCargado = false; // Marcar para recargar

                if (typeof contarTareaPublicidad === 'function') {
                    contarTareaPublicidad('vision');
                }
            } else {
                mostrarErrorVision(data.message || 'Error al analizar imagen');
            }
        } catch (error) {
            mostrarErrorVision('No se pudo conectar con el servidor');
            if (CONFIG.DEBUG) console.error('Error vision:', error);
        }
    };

    reader.readAsDataURL(imagenSeleccionada);
}

// ==========================================
// Mostrar análisis
// ==========================================
function mostrarAnalisis(imagenBase64, respuesta) {
    const resultado = document.getElementById('vision-resultado');
    resultado.innerHTML = `
        <div class="vision-resultado-completo">
            <img src="${imagenBase64}" alt="Imagen analizada" class="preview-img">
            <div class="analisis-buho">
                <h3>🦉 Análisis del búho:</h3>
                <div class="analisis-texto">${formatearTextoVision(respuesta)}</div>
            </div>
            <div class="imagen-acciones">
                <button onclick="volverAHistorialVision()" class="btn-otra">
                    📚 Ver historial
                </button>
                <button onclick="analizarOtraFoto()" class="btn-otra">
                    📸 Analizar otra foto
                </button>
            </div>
        </div>
    `;

    renderizarMatematicasVision(resultado);
}

// ==========================================
// Mostrar error
// ==========================================
function mostrarErrorVision(mensaje) {
    const resultado = document.getElementById('vision-resultado');
    resultado.innerHTML = `
        <div class="mensaje-error">
            ❌ ${mensaje}
        </div>
    `;
}

// ==========================================
// Limpiar y empezar de nuevo
// ==========================================
function analizarOtraFoto() {
    imagenSeleccionada = null;
    document.getElementById('vision-file').value = '';
    document.getElementById('vision-input').value = '';
    document.getElementById('vision-resultado').innerHTML = '';
    // Cargar historial de nuevo
    historialVisionCargado = false;
    setTimeout(cargarHistorialVision, 300);
}

// ==========================================
// 🧮 Normalizar LaTeX
// ==========================================
function normalizarLatexVision(texto) {
    texto = texto.replace(/\(\((.+?)\)\)/g, '$$$1$$');
    texto = texto.replace(/\((\\[a-zA-Z]+.*?)\)/g, '$$$1$$');
    texto = texto.replace(/\\\((.+?)\\\)/g, '$$$1$$');
    texto = texto.replace(/\\\[(.+?)\\\]/g, '$$$$$1$$$$');
    return texto;
}

// ==========================================
// Formatear texto Markdown
// ==========================================
function formatearTextoVision(texto) {
    texto = normalizarLatexVision(texto);

    if (typeof marked !== 'undefined') {
        marked.setOptions({
            breaks: true,
            gfm: true
        });
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
function renderizarMatematicasVision(elemento) {
    if (window.MathJax && window.MathJax.typesetPromise) {
        window.MathJax.typesetPromise([elemento]).catch(function(err) {
            if (CONFIG.DEBUG) console.error('MathJax error:', err);
        });
    }
}

if (CONFIG.DEBUG) console.log('🔍 vision.js V3.0 cargado');
