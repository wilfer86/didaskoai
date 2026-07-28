// ==========================================
// vision.js - Didasko AI
// Analizar fotos con NVIDIA/Gemini Vision
// ==========================================

let imagenSeleccionada = null;

// Cuando el usuario selecciona una imagen
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
});

// Manejar cuando eligen un archivo
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

// Mostrar preview de la imagen seleccionada
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

// Función principal: analizar imagen
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
            const response = await fetch(apiUrl('/api/vision/analizar'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    imagen_base64: imagenBase64,
                    prompt: prompt || 'Analiza esta imagen y ayúdame con lo que ves. Explica paso a paso.'
                })
            });

            const data = await response.json();

            if (data.success) {
                mostrarAnalisis(imagenBase64, data.respuesta);

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

// Mostrar el análisis del búho
function mostrarAnalisis(imagenBase64, respuesta) {
    const resultado = document.getElementById('vision-resultado');
    resultado.innerHTML = `
        <div class="vision-resultado-completo">
            <img src="${imagenBase64}" alt="Imagen analizada" class="preview-img">
            <div class="analisis-buho">
                <h3>🦉 Análisis del búho:</h3>
                <div class="analisis-texto">${formatearTextoVision(respuesta)}</div>
            </div>
            <button onclick="analizarOtraFoto()" class="btn-otra">
                📸 Analizar otra foto
            </button>
        </div>
    `;

    // 🧮 Renderizar fórmulas matemáticas con MathJax
    renderizarMatematicasVision(resultado);
}

// Mostrar error
function mostrarErrorVision(mensaje) {
    const resultado = document.getElementById('vision-resultado');
    resultado.innerHTML = `
        <div class="mensaje-error">
            ❌ ${mensaje}
        </div>
    `;
}

// Limpiar y empezar de nuevo
function analizarOtraFoto() {
    imagenSeleccionada = null;
    document.getElementById('vision-file').value = '';
    document.getElementById('vision-input').value = '';
    document.getElementById('vision-resultado').innerHTML = '';
}

// 🧮 Normalizar LaTeX (arregla el formato raro de NVIDIA)
function normalizarLatexVision(texto) {
    texto = texto.replace(/\(\((.+?)\)\)/g, '$$$1$$');
    texto = texto.replace(/\((\\[a-zA-Z]+.*?)\)/g, '$$$1$$');
    texto = texto.replace(/\\\((.+?)\\\)/g, '$$$1$$');
    texto = texto.replace(/\\\[(.+?)\\\]/g, '$$$$$1$$$$');
    return texto;
}

// Formatear texto usando marked.js
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

// 🧮 Renderizar fórmulas matemáticas
function renderizarMatematicasVision(elemento) {
    if (window.MathJax && window.MathJax.typesetPromise) {
        window.MathJax.typesetPromise([elemento]).catch(function(err) {
            if (CONFIG.DEBUG) console.error('MathJax error:', err);
        });
    }
}

if (CONFIG.DEBUG) console.log('🔍 vision.js cargado');
