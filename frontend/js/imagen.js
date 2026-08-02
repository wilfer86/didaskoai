// ==========================================
// imagen.js - Didasko AI
// Crear y Editar imágenes
// ==========================================

// Estado global
let modoImagenActual = 'crear';       // 'crear' o 'editar'
let formatoImagenActual = '1:1';
let imagenParaEditar = null;          // base64 de la imagen subida

// ==========================================
// Seleccionar modo (Crear / Editar)
// ==========================================
function seleccionarModo(modo) {
    modoImagenActual = modo;

    document.querySelectorAll('.btn-modo').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.modo === modo);
    });

    const formatoSelector = document.getElementById('formato-selector');
    const btnSubir = document.getElementById('btn-subir-imagen');
    const input = document.getElementById('imagen-input');
    const resultado = document.getElementById('imagen-resultado');

    if (modo === 'crear') {
        formatoSelector.style.display = 'flex';
        btnSubir.style.display = 'none';
        input.placeholder = 'Describe tu imagen...';
        imagenParaEditar = null;
        resultado.innerHTML = '';
    } else {
        formatoSelector.style.display = 'none';
        btnSubir.style.display = 'inline-block';
        input.placeholder = 'Describe cómo transformar la imagen...';
        resultado.innerHTML = `
            <div class="editar-hint">
                <div class="aviso-experimental">
                    <p>🧪 <strong>Función experimental en aprendizaje</strong></p>
                    <p class="aviso-sub">Este modelo aún está en fase de pruebas.<br>Los resultados pueden variar y no siempre serán perfectos.</p>
                </div>
                <p>🎨 Modo <strong>Editar / Transformar</strong></p>
                <p>1️⃣ Sube una imagen con 📤</p>
                <p>2️⃣ Escribe cómo quieres transformarla</p>
                <p>3️⃣ Presiona ➤</p>
                <div class="tips-edicion">
                    <p>💡 <strong>Tips para mejores resultados:</strong></p>
                    <p>✅ "Convertir a estilo pintura al óleo"</p>
                    <p>✅ "Agregar fondo espacial"</p>
                    <p>✅ "Estilo anime japonés"</p>
                    <p>✅ "Cambiar a blanco y negro artístico"</p>
                    <p>❌ Evita instrucciones muy precisas (ej: "solo cambia el ojo derecho")</p>
                </div>
            </div>
        `;
    }

    if (CONFIG.DEBUG) console.log('🎨 Modo:', modo);
}

// ==========================================
// Seleccionar formato (1:1, 16:9, 9:16)
// ==========================================
function seleccionarFormato(formato) {
    formatoImagenActual = formato;

    document.querySelectorAll('.btn-formato').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.formato === formato);
    });

    if (CONFIG.DEBUG) console.log('🖼️ Formato:', formato);
}

// ==========================================
// Manejar carga de imagen para editar
// ==========================================
function manejarImagenEditar(evento) {
    const archivo = evento.target.files[0];
    if (!archivo) return;

    if (!archivo.type.startsWith('image/')) {
        mostrarImagenError('El archivo debe ser una imagen');
        return;
    }

    if (archivo.size > 10 * 1024 * 1024) {
        mostrarImagenError('Imagen muy grande (máximo 10 MB)');
        return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
        imagenParaEditar = e.target.result;

        const resultado = document.getElementById('imagen-resultado');
        resultado.innerHTML = `
            <div class="editar-preview">
                <img src="${imagenParaEditar}" alt="Imagen a editar" class="preview-img">
                <p class="preview-hint">✅ Imagen cargada. Ahora escribe cómo transformarla y presiona ➤</p>
                <p class="aviso-mini">🧪 Recuerda: modelo experimental, los resultados pueden variar</p>
            </div>
        `;
    };
    reader.readAsDataURL(archivo);
}

// ==========================================
// Router: decide si crear o editar
// ==========================================
function procesarImagen() {
    if (modoImagenActual === 'crear') {
        crearImagen();
    } else {
        editarImagen();
    }
}

// ==========================================
// CREAR imagen
// ==========================================
async function crearImagen() {
    const input = document.getElementById('imagen-input');
    const resultado = document.getElementById('imagen-resultado');
    const prompt = input.value.trim();

    if (!prompt) {
        mostrarImagenError('Escribe una descripción de la imagen');
        return;
    }

    resultado.innerHTML = `
        <div class="loader-imagen">
            <span class="loader"></span>
            <p>🦉 Creando con Didasko AI...</p>
            <p class="texto-espera">Esto puede tomar entre 10 y 60 segundos</p>
        </div>
    `;

    input.value = '';

    try {
        const response = await fetch(apiUrl('/api/imagen/crear'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: prompt,
                formato: formatoImagenActual
            })
        });

        const data = await response.json();

        if (data.success && data.imagen_url) {
            mostrarImagen(data.imagen_url, prompt, formatoImagenActual, data.proveedor);

            if (typeof contarTareaPublicidad === 'function') {
                contarTareaPublicidad('imagen');
            }
        } else {
            mostrarImagenError(data.message || 'Error al crear imagen');
        }
    } catch (error) {
        mostrarImagenError('No se pudo conectar con el servidor');
        if (CONFIG.DEBUG) console.error('Error crear imagen:', error);
    }
}

// ==========================================
// EDITAR imagen
// ==========================================
async function editarImagen() {
    const input = document.getElementById('imagen-input');
    const resultado = document.getElementById('imagen-resultado');
    const prompt = input.value.trim();

    if (!imagenParaEditar) {
        mostrarImagenError('Primero sube una imagen con 📤');
        return;
    }

    if (!prompt) {
        mostrarImagenError('Describe cómo quieres transformar la imagen');
        return;
    }

    resultado.innerHTML = `
        <div class="loader-imagen">
            <img src="${imagenParaEditar}" alt="Editando" class="preview-img" style="opacity:0.5">
            <span class="loader"></span>
            <p>🦉 Transformando con Didasko AI...</p>
            <p class="texto-espera">🧪 Modelo experimental — Esto puede tomar entre 30 y 90 segundos</p>
        </div>
    `;

    input.value = '';

    try {
        const response = await fetch(apiUrl('/api/imagen/editar'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: prompt,
                imagen_base64: imagenParaEditar
            })
        });

        const data = await response.json();

        if (data.success && data.imagen_url) {
            mostrarImagenEditada(data.imagen_url, prompt, data.proveedor);

            if (typeof contarTareaPublicidad === 'function') {
                contarTareaPublicidad('imagen');
            }
        } else {
            mostrarImagenError(data.message || 'Error al editar imagen');
        }
    } catch (error) {
        mostrarImagenError('No se pudo conectar con el servidor');
        if (CONFIG.DEBUG) console.error('Error editar imagen:', error);
    }
}

// ==========================================
// Mostrar imagen CREADA
// ==========================================
function mostrarImagen(url, prompt, formato, proveedor) {
    const resultado = document.getElementById('imagen-resultado');
    const claseFormato = `formato-${formato.replace(':', '-')}`;

    resultado.innerHTML = `
        <div class="imagen-generada">
            <img src="${url}" alt="Imagen generada" class="imagen-resultado-img ${claseFormato}">
            <div class="imagen-info">
                <p class="prompt-usado">📝 "${prompt}"</p>
                <p class="formato-usado">🖼️ ${formato} | ⚡ ${proveedor} | 🦉 Didasko AI</p>
                <div class="imagen-acciones">
                    <a href="${url}" download="didasko-imagen.png" target="_blank" class="btn-descargar">
                        📥 Descargar
                    </a>
                    <button onclick="editarEstaImagen('${url}')" class="btn-otra">
                        🎨 Transformar esta
                    </button>
                    <button onclick="crearOtraImagen()" class="btn-otra">
                        🔄 Crear otra
                    </button>
                </div>
            </div>
        </div>
    `;
}

// ==========================================
// Mostrar imagen EDITADA
// ==========================================
function mostrarImagenEditada(url, prompt, proveedor) {
    const resultado = document.getElementById('imagen-resultado');

    resultado.innerHTML = `
        <div class="imagen-generada">
            <img src="${url}" alt="Imagen editada" class="imagen-resultado-img">
            <div class="imagen-info">
                <p class="prompt-usado">🎨 Transformación: "${prompt}"</p>
                <p class="formato-usado">⚡ ${proveedor} | 🦉 Didasko AI</p>
                <p class="aviso-resultado">🧪 Resultado experimental — Modelo en aprendizaje</p>
                <div class="imagen-acciones">
                    <a href="${url}" download="didasko-transformada.png" target="_blank" class="btn-descargar">
                        📥 Descargar
                    </a>
                    <button onclick="editarEstaImagen('${url}')" class="btn-otra">
                        🎨 Transformar de nuevo
                    </button>
                    <button onclick="crearOtraImagen()" class="btn-otra">
                        🔄 Empezar otra
                    </button>
                </div>
            </div>
        </div>
    `;
}

// ==========================================
// Usar imagen recién creada para editarla
// ==========================================
function editarEstaImagen(url) {
    imagenParaEditar = url;
    seleccionarModo('editar');

    const resultado = document.getElementById('imagen-resultado');
    resultado.innerHTML = `
        <div class="editar-preview">
            <img src="${url}" alt="Imagen a editar" class="preview-img">
            <p class="preview-hint">✅ Imagen lista para transformar. Escribe cómo quieres modificarla y presiona ➤</p>
            <p class="aviso-mini">🧪 Recuerda: modelo experimental, los resultados pueden variar</p>
        </div>
    `;

    document.getElementById('imagen-input').focus();
}

// ==========================================
// Mostrar error
// ==========================================
function mostrarImagenError(mensaje) {
    const resultado = document.getElementById('imagen-resultado');
    resultado.innerHTML = `
        <div class="mensaje-error">
            ❌ ${mensaje}
        </div>
    `;
}

// ==========================================
// Limpiar y volver a intentar
// ==========================================
function crearOtraImagen() {
    const resultado = document.getElementById('imagen-resultado');
    resultado.innerHTML = '';
    imagenParaEditar = null;
    document.getElementById('imagen-input').focus();
}

// ==========================================
// Compatibilidad con función vieja
// ==========================================
function actualizarFormatoImagen(formato) {
    seleccionarFormato(formato);
}

// ==========================================
// Inicialización
// ==========================================
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('imagen-input');
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                procesarImagen();
            }
        });
    }

    const fileEditar = document.getElementById('imagen-editar-file');
    if (fileEditar) {
        fileEditar.addEventListener('change', manejarImagenEditar);
    }
});

if (CONFIG.DEBUG) console.log('🎨 imagen.js cargado (Crear + Editar)');
