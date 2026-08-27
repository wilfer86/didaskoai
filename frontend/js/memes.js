// ===================================
// memes.js - Lógica del Generador de Memes
// ===================================

let guionesGenerados = [];

function mostrarNombreArchivo(input) {
    if (input.files && input.files[0]) {
        document.getElementById('nombre-archivo').textContent = `📎 ${input.files[0].name}`;
        document.getElementById('btn-procesar').style.display = 'inline-block';
    }
}

async function procesarMeme() {
    const fileInput = document.getElementById('meme-file');
    if (!fileInput.files || !fileInput.files[0]) return;

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    // UI: Mostrar loader
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
            renderizarGuiones(guionesGenerados);
        } else {
            alert('❌ Error: ' + data.error);
        }
    } catch (error) {
        alert('❌ Error de conexión: ' + error.message);
    } finally {
        document.getElementById('memes-loader').style.display = 'none';
    }
}

function renderizarGuiones(guiones) {
    const contenedor = document.getElementById('memes-resultados');
    contenedor.innerHTML = '';

    guiones.forEach((guion, index) => {
        const card = document.createElement('div');
        card.className = 'meme-card';
        card.style.cssText = 'border: 1px solid #ddd; border-radius: 12px; padding: 15px; background: #fff; box-shadow: 0 4px 6px rgba(0,0,0,0.1);';
        
        card.innerHTML = `
            <h4 style="margin-top: 0; color: #e74c3c;">${index + 1}. ${guion.titulo}</h4>
            <p style="font-size: 0.9em; color: #555;"><strong>Situación:</strong> ${guion.situacion}</p>
            <div style="background: #f0f0f0; padding: 10px; border-radius: 8px; margin: 10px 0; text-align: center;">
                <p style="margin: 0; font-weight: bold; color: #333;">${guion.texto_superior}</p>
                <div style="height: 100px; background: #ddd; margin: 10px 0; display: flex; align-items: center; justify-content: center; color: #777; border-radius: 4px;" id="img-preview-${index}">
                    Sin imagen
                </div>
                <p style="margin: 0; font-weight: bold; color: #333;">${guion.texto_inferior}</p>
            </div>
            <button onclick="generarImagenMeme(${index}, this)" class="btn-generar-img" style="width: 100%; padding: 10px; background: #0088cc; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">
                🎨 Generar esta Imagen
            </button>
        `;
        contenedor.appendChild(card);
    });
}

async function generarImagenMeme(index, boton) {
    const guion = guionesGenerados[index];
    const previewDiv = document.getElementById(`img-preview-${index}`);
    
    boton.disabled = true;
    boton.textContent = '⏳ Generando...';
    previewDiv.innerHTML = '<div class="loader" style="width: 30px; height: 30px;"></div>';

    try {
        const response = await fetch('/api/memes/generar-imagen', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: guion.prompt_imagen })
        });

        const data = await response.json();

        if (data.success) {
            previewDiv.innerHTML = `<img src="${data.imagen_url}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 4px;" alt="Meme generado">`;
            boton.textContent = '✅ ¡Listo! (Clic derecho para guardar)';
            boton.style.background = '#27ae60';
        } else {
            previewDiv.innerHTML = '❌ Error';
            boton.disabled = false;
            boton.textContent = '🔄 Reintentar';
        }
    } catch (error) {
        previewDiv.innerHTML = '❌ Error';
        boton.disabled = false;
        boton.textContent = '🔄 Reintentar';
    }
}
