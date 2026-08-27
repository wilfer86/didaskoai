// ===================================
// memes.js - Generador de Memes Virales con IA
// Versión: 1.0 - Soporta VIDEO e IMAGEN
// ===================================

let guionesGenerados = [];
let memeArchivo = null;

// Mostrar nombre del archivo seleccionado
function mostrarNombreArchivo(input) {
    if (input.files && input.files[0]) {
        memeArchivo = input.files[0];
        const esVideo = memeArchivo.type.startsWith('video/');
        const tipoTexto = esVideo ? '🎬 Video' : ' Imagen';
        const tamañoMB = (memeArchivo.size / (1024 * 1024)).toFixed(2);
        
        // Advertencia si el video es muy grande
        if (esVideo && memeArchivo.size > 10 * 1024 * 1024) {
            alert('⚠️ El video es muy grande (>10MB). Puede tardar más o fallar. Considera comprimirlo.');
        }
        
        document.getElementById('nombre-archivo').innerHTML = 
            `${tipoTexto}: <strong>${memeArchivo.name}</strong> (${tamañoMB} MB)`;
        document.getElementById('btn-procesar').style.display = 'inline-block';
    }
}

// Procesar el meme (analizar y generar guiones)
async function procesarMeme() {
    if (!memeArchivo) {
        alert('❌ Por favor selecciona un archivo primero');
        return;
    }

    const formData = new FormData();
    formData.append('file', memeArchivo);

    // Mostrar loader
    document.getElementById('btn-procesar').style.display = 'none';
    document.getElementById('memes-loader').style.display = 'block';
    document.getElementById('memes-resultados').innerHTML = '';

    try {
        const response = await fetch('/api/memes/analizar', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            guionesGenerados = data.guiones;
            const tipoArchivo = data.tipo_archivo || 'contenido';
            console.log(`✅ Análisis completado: ${guionesGenerados.length} guiones generados para ${tipoArchivo}`);
            renderizarGuiones(guionesGenerados);
        } else {
            alert('❌ Error: ' + data.error);
            document.getElementById('btn-procesar').style.display = 'inline-block';
        }
    } catch (error) {
        console.error('Error al procesar meme:', error);
        alert('❌ Error de conexión: ' + error.message);
        document.getElementById('btn-procesar').style.display = 'inline-block';
    } finally {
        document.getElementById('memes-loader').style.display = 'none';
    }
}

// Renderizar los guiones generados
function renderizarGuiones(guiones) {
    const contenedor = document.getElementById('memes-resultados');
    contenedor.innerHTML = '';

    if (!guiones || guiones.length === 0) {
        contenedor.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #666; grid-column: 1/-1;">
                <p style="font-size: 1.2em;"> No se generaron guiones</p>
                <p>Intenta subir otro meme o verifica que el archivo sea válido</p>
            </div>
        `;
        return;
    }

    guiones.forEach((guion, index) => {
        const card = document.createElement('div');
        card.className = 'meme-card';
        card.style.cssText = `
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            padding: 20px;
            background: #fff;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        `;
        
        // Efecto hover
        card.onmouseenter = () => {
            card.style.transform = 'translateY(-5px)';
            card.style.boxShadow = '0 8px 15px rgba(0,0,0,0.2)';
        };
        card.onmouseleave = () => {
            card.style.transform = 'translateY(0)';
            card.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
        };
        
        card.innerHTML = `
            <h4 style="margin: 0 0 15px 0; color: #e74c3c; font-size: 1.2em; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px;">
                ${index + 1}. ${guion.titulo || 'Meme ' + (index + 1)}
            </h4>
            
            <div style="margin-bottom: 15px;">
                <p style="font-size: 0.95em; color: #555; margin: 8px 0; line-height: 1.5;">
                    <strong style="color: #333;">📝 Situación:</strong><br>
                    ${guion.situacion || 'Sin descripción'}
                </p>
            </div>
            
            <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                        padding: 15px; border-radius: 10px; margin: 15px 0; text-align: center;
                        border: 1px solid #ddd;">
                
                <p style="margin: 0 0 10px 0; font-weight: bold; color: #2c3e50; font-size: 1em;">
                    ${guion.texto_superior || ''}
                </p>
                
                <div style="height: 180px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            margin: 10px 0; display: flex; align-items: center; justify-content: center; 
                            color: white; border-radius: 8px; font-size: 1em; cursor: pointer;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);" 
                     id="img-preview-${index}"
                     onclick="generarImagenMeme(${index}, this)">
                    <div style="text-align: center;">
                        <div style="font-size: 3em; margin-bottom: 10px;">🎨</div>
                        <div style="font-weight: bold;">Click para generar imagen</div>
                        <div style="font-size: 0.85em; margin-top: 5px; opacity: 0.9;">IA generará esta imagen</div>
                    </div>
                </div>
                
                <p style="margin: 10px 0 0 0; font-weight: bold; color: #2c3e50; font-size: 1em;">
                    ${guion.texto_inferior || ''}
                </p>
            </div>
            
            <button onclick="generarImagenMeme(${index}, this)" 
                    class="btn-generar-img"
                    style="width: 100%; 
                           padding: 12px; 
                           background: linear-gradient(135deg, #0088cc, #005a8f); 
                           color: white; 
                           border: none; 
                           border-radius: 8px; 
                           cursor: pointer; 
                           font-weight: bold; 
                           font-size: 1em;
                           transition: all 0.3s;
                           box-shadow: 0 4px 6px rgba(0,136,204,0.3);">
                🎨 Generar Imagen con IA
            </button>
        `;
        
        contenedor.appendChild(card);
    });
    
    // Mostrar mensaje de éxito
    const mensaje = document.createElement('div');
    mensaje.style.cssText = `
        grid-column: 1/-1;
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        border: 2px solid #28a745;
        margin-bottom: 20px;
    `;
    mensaje.innerHTML = `
        <strong style="color: #155724; font-size: 1.1em;">
            ✅ ¡Se generaron ${guiones.length} guiones absurdos!
        </strong>
        <p style="margin: 5px 0 0 0; color: #155724;">
            Haz clic en "Generar Imagen" en cada tarjeta para crear el meme visual
        </p>
    `;
    contenedor.insertBefore(mensaje, contenedor.firstChild);
}

// Generar imagen para un guión específico
async function generarImagenMeme(index, elemento) {
    if (!guionesGenerados[index]) {
        alert('❌ Guión no encontrado');
        return;
    }
    
    const guion = guionesGenerados[index];
    
    // Encontrar el div de preview y el botón
    let previewDiv, boton;
    
    if (elemento.id && elemento.id.startsWith('img-preview-')) {
        previewDiv = elemento;
        boton = document.querySelector(`button[onclick="generarImagenMeme(${index}, this)"]`);
    } else {
        // Si se hizo clic en el botón, buscar el preview
        boton = elemento;
        previewDiv = document.getElementById(`img-preview-${index}`);
    }
    
    if (!previewDiv || !boton) {
        console.error('No se encontraron los elementos DOM');
        return;
    }
    
    // Deshabilitar y mostrar loading
    boton.disabled = true;
    const textoOriginal = boton.textContent;
    boton.textContent = '⏳ Generando...';
    boton.style.background = '#95a5a6';
    boton.style.cursor = 'not-allowed';
    
    previewDiv.innerHTML = `
        <div style="text-align: center; color: white;">
            <div style="border: 4px solid rgba(255,255,255,0.3); 
                        border-top: 4px solid white; 
                        border-radius: 50%; 
                        width: 50px; 
                        height: 50px; 
                        animation: spin 1s linear infinite;
                        margin: 0 auto 15px;"></div>
            <div style="font-weight: bold; font-size: 1.1em;">Generando con IA...</div>
            <div style="font-size: 0.9em; margin-top: 5px; opacity: 0.9;">Esto puede tomar 10-20 segundos</div>
        </div>
    `;

    try {
        const prompt = guion.prompt_imagen || guion.situacion || 'viral meme funny situation';
        
        const response = await fetch('/api/memes/generar-imagen', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: prompt })
        });

        const data = await response.json();

        if (data.success && data.imagen_url) {
            // Imagen generada exitosamente
            previewDiv.innerHTML = `
                <img src="${data.imagen_url}" 
                     style="width: 100%; 
                            height: 100%; 
                            object-fit: cover; 
                            border-radius: 8px;
                            box-shadow: 0 4px 8px rgba(0,0,0,0.2);" 
                     alt="Meme generado"
                     onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22180%22%3E%3Crect fill=%22%23ddd%22 width=%22200%22 height=%22180%22/%3E%3Ctext fill=%22%23999%22 x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22%3Error al cargar%3C/text%3E%3C/svg%3E'">
            `;
            
            boton.textContent = '✅ ¡Imagen Lista!';
            boton.style.background = 'linear-gradient(135deg, #27ae60, #1e8449)';
            boton.style.cursor = 'pointer';
            
            // Agregar mensaje de descarga
            const mensajeDescarga = document.createElement('div');
            mensajeDescarga.style.cssText = `
                grid-column: 1/-1;
                background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
                padding: 10px;
                border-radius: 6px;
                text-align: center;
                margin-top: 10px;
                border: 1px solid #0c5460;
            `;
            mensajeDescarga.innerHTML = `
                <strong style="color: #0c5460;">💡 Tip:</strong>
                <span style="color: #0c5460; margin-left: 5px;">
                    Haz clic derecho en la imagen → "Guardar imagen como" para descargar
                </span>
            `;
            
            if (!previewDiv.nextElementSibling || !previewDiv.nextElementSibling.classList.contains('tip-descarga')) {
                mensajeDescarga.classList.add('tip-descarga');
                previewDiv.parentNode.insertBefore(mensajeDescarga, previewDiv.nextSibling);
            }
            
        } else {
            throw new Error(data.error || 'Error al generar imagen');
        }
        
    } catch (error) {
        console.error('Error generando imagen:', error);
        previewDiv.innerHTML = `
            <div style="text-align: center; color: white; padding: 20px;">
                <div style="font-size: 3em; margin-bottom: 10px;">❌</div>
                <div style="font-weight: bold;">Error al generar</div>
                <div style="font-size: 0.9em; margin-top: 5px; opacity: 0.9;">${error.message}</div>
            </div>
        `;
        
        boton.disabled = false;
        boton.textContent = '🔄 Reintentar';
        boton.style.background = 'linear-gradient(135deg, #f39c12, #d68910)';
        boton.style.cursor = 'pointer';
    }
}

// Función para volver al inicio (si es necesario)
function volverAlInicioMemes() {
    if (confirm('¿Quieres limpiar todo y empezar de nuevo?')) {
        guionesGenerados = [];
        memeArchivo = null;
        document.getElementById('meme-file').value = '';
        document.getElementById('nombre-archivo').textContent = '';
        document.getElementById('btn-procesar').style.display = 'none';
        document.getElementById('memes-resultados').innerHTML = '';
    }
}

// Animación CSS para el spinner
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .meme-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.2);
    }
`;
document.head.appendChild(style);

console.log('✅ memes.js cargado - Generador de Memes Virales v1.0');
