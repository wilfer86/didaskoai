// ==========================================
// imagen.js - Didasko AI V3.0
// Crear/Editar imágenes + Galería persistente
// ==========================================

let modoImagenActual = 'crear';
let formatoImagenActual = '1:1';
let imagenParaEditar = null;
let galeriaCargada = false;

// ==========================================
// 🔄 Cargar galería de imágenes previas
// ==========================================
async function cargarGaleriaImagenes() {
    if (galeriaCargada) return;

    try {
        const response = await fetch('/api/imagen/historial?limite=12', {
            credentials: 'include'
        });
        const data = await response.json();

        if (data.success && data.imagenes && data.imagenes.length > 0) {
            mostrarGaleria(data.imagenes);
        }

        galeriaCargada = true;
    } catch (error) {
        if (CONFIG.DEBUG) console.warn('No se cargó galería:', error);
    }
}

// ==========================================
// 🖼️ Mostrar galería de imágenes previas
// ==========================================
function mostrarGaleria(imagenes) {
    const resultado = document.getElementById('imagen-resultado');
    if (!resultado) return;

    // Solo mostrar si estamos en modo crear y no hay contenido
    if (modoImagenActual !== 'crear' || resultado.innerHTML.trim() !== '') return;

    const htmlGaleria = `
        <div class="galeria-imagenes">
            <h3 class="galeria-titulo">🎨 Tus imágenes anteriores</h3>
            <div class="galeria-grid">
                ${imagenes.map(img => `
                    <div class="galeria-item" onclick="verImagenCompleta('${img.id}', '${img.url}', ${JSON.stringify(img.prompt).replace(/"/g, '&quot;')}, '${img.tipo}')">
                        <img src="${img.url}" alt="${img.prompt}" loading="lazy">
                        <div class="galeria-info">
                            <span class="galeria-tipo">${img.tipo === 'creada' ? '🎨' : img.tipo === 'editada' ? '✏️' : '🔍'}</span>
                            <p class="galeria-prompt">${img.prompt.substring(0, 40)}${img.prompt.length > 40 ? '...' : ''}</p>
                        </div>
                    </div>
                `).join('')}
            </div>
            <p class="galeria-hint">👆 Toca una imagen para verla completa</p>
        </div>
    `;

    resultado.innerHTML = htmlGaleria;
}

// ==========================================
// 🔍 Ver imagen completa desde galería
// ==========================================
function verImagenCompleta(id, url, prompt, tipo) {
    const resultado = document.getElementById('imagen-resultado');
    const iconoTipo = tipo === 'creada' ? '🎨 Creada' : tipo === 'editada' ? '✏️ Editada' : '🔍 Analizada';

    resultado.innerHTML = `
        <div class="imagen-generada">
            <img src="${url}" alt="Imagen" class="imagen-resultado-img">
            <div class="imagen-info">
                <p class="prompt-usado">📝 "${prompt}"</p>
                <p class="formato-usado">${iconoTipo} | 🦉 Didasko AI</p>
                <div class="imagen-acciones">
                    <a href="${url}" download="didasko-imagen.png" target="_blank" class="btn-descargar">
                        📥 Descargar
                    </a>
                    <button onclick="editarEstaImagen('${url}')" class="btn-otra">
                        🎨 Transformar
                    </button>
                    <button onclick="volverAGaleria()" class="btn-otra">
                        🖼️ Ver galería
                    </button>
                    <button onclick="eliminarImagenGaleria('${id}')" class="btn-otra" style="background: linear-gradient(135deg, #e74c3c, #c0392b); color: white;">
                        🗑️ Eliminar
                    </button>
                </div>
            </div>
        </div>
    `;
}

// ==========================================
// 🗑️ Eliminar imagen de galería
// ==========================================
async function eliminarImagenGaleria(imagenId) {
    if (!confirm('🤔 ¿Eliminar esta imagen del historial?')) return;

    try {
        await fetch(`/api/imagen/eliminar/${imagenId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        galeriaCargada = false;
        volverAGaleria();
    } catch (error) {
        if (CONFIG.DEBUG) console.error('Error eliminando:', error);
    }
}

// ==========================================
// 🖼️ Volver a la galería
// ==========================================
function volverAGaleria() {
    galeriaCargada = false;
    const resultado = document.getElementById('imagen-resultado');
    resultado.innerHTML = '';
    cargarGaleriaImagenes();
}

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
        // Recargar galería al volver a crear
        galeriaCargada = false;
        setTimeout(cargarGaleriaImagenes, 300);
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
}

// ==========================================
// Seleccionar formato
// ==========================================
function seleccionarFormato(formato) {
    formatoImagenActual = formato;
    document.querySelectorAll('.btn-formato').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.formato === formato);
    });
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
                <p class="preview-hint">✅ Imagen cargada. Escribe cómo transformarla y presiona ➤</p>
                <p class="aviso-mini">🧪 Recuerda: modelo experimental</p>
            </div>
        `;
    };
    reader.readAsDataURL(archivo);
}

// ==========================================
// Router: crear o editar
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
        const response = await fetch('/api/imagen/crear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                prompt: prompt,
                formato: formatoImagenActual
            })
        });

        const data = await response.json();

        if (data.success && data.imagen_url) {
            mostrarImagen(data.imagen_url, prompt, formatoImagenActual, data.proveedor);
            galeriaCargada = false; // Marcar galería para recargar

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
            <p class="texto-espera">🧪 Modelo experimental — 30 a 90 segundos</p>
        </div>
    `;

    input.value = '';

    try {
        const response = await fetch('/api/imagen/editar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                prompt: prompt,
                imagen_base64: imagenParaEditar
            })
        });

        const data = await response.json();

        if (data.success && data.imagen_url) {
            mostrarImagenEditada(data.imagen_url, prompt, data.proveedor);
            galeriaCargada = false;

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
                    <button onclick="volverAGaleria()" class="btn-otra">
                        🖼️ Ver galería
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
                <p class="aviso-resultado">🧪 Resultado experimental</p>
                <div class="imagen-acciones">
                    <a href="${url}" download="didasko-transformada.png" target="_blank" class="btn-descargar">
                        📥 Descargar
                    </a>
                    <button onclick="editarEstaImagen('${url}')" class="btn-otra">
                        🎨 Transformar de nuevo
                    </button>
                    <button onclick="volverAGaleria()" class="btn-otra">
                        🖼️ Ver galería
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
            <p class="preview-hint">✅ Imagen lista para transformar. Escribe cómo modificarla</p>
            <p class="aviso-mini">🧪 Modelo experimental</p>
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
// Limpiar
// ==========================================
function crearOtraImagen() {
    const resultado = document.getElementById('imagen-resultado');
    resultado.innerHTML = '';
    imagenParaEditar = null;
    document.getElementById('imagen-input').focus();
    // Recargar galería
    galeriaCargada = false;
    setTimeout(cargarGaleriaImagenes, 300);
}

// Compatibilidad
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

    // Cargar galería después de 1 seg
    setTimeout(cargarGaleriaImagenes, 1500);
});

if (CONFIG.DEBUG) console.log('🎨 imagen.js V3.0 cargado');
