// ===================================
// profeta.js - Didasko AI V3.3
// Profeta Deportivo 🌐 con predicciones IA
// ===================================

let ligaSeleccionada = null;
let profetaCargado = false;

// ===================================
// 🌐 Cargar Profeta al abrir sección
// ===================================
async function cargarProfeta() {
    if (profetaCargado) return;
    mostrarPartidosHoy();
    profetaCargado = true;
}

// ===================================
// 🌐 Mostrar partidos del día + ligas
// ===================================
async function mostrarPartidosHoy() {
    const contenedor = document.getElementById('profeta-resultado');
    if (!contenedor) return;

    contenedor.innerHTML = `
        <div class="profeta-loader">
            <span class="loader"></span>
            <p>🦉 Consultando el Profeta Deportivo...</p>
        </div>
    `;

    try {
        const [partidosRes, ligasRes] = await Promise.all([
            fetch('/api/profeta/hoy', { credentials: 'include' }),
            fetch('/api/profeta/ligas', { credentials: 'include' })
        ]);

        const data = await partidosRes.json();
        const ligasData = await ligasRes.json();

        renderizarProfeta(data, ligasData);
    } catch (error) {
        contenedor.innerHTML = `
            <div class="mensaje-error">
                ❌ Error cargando el Profeta: ${error.message}
            </div>
        `;
    }
}

// ===================================
// 🌐 Renderizar Profeta principal
// ===================================
function renderizarProfeta(dataPartidos, dataLigas) {
    const contenedor = document.getElementById('profeta-resultado');
    if (!contenedor) return;

    const fecha = new Date().toLocaleDateString('es-CO', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });

    // Estado de partidos hoy
    let htmlPartidosHoy = '';
    if (dataPartidos.success && dataPartidos.partidos && dataPartidos.partidos.length > 0) {
        htmlPartidosHoy = `
            <div class="profeta-partidos-hoy">
                <h3 class="profeta-subtitulo">🏆 Partidos de hoy</h3>
                <div class="partidos-lista">
                    ${dataPartidos.partidos.map(p => renderizarPartido(p)).join('')}
                </div>
            </div>
        `;
    } else {
        htmlPartidosHoy = `
            <div class="profeta-info-banner">
                <div class="info-item">
                    <span class="info-icono">📅</span>
                    <div class="info-texto">
                        <p><strong>No hay partidos de ligas prioritarias hoy</strong></p>
                        <p class="mini">Selecciona una liga abajo</p>
                    </div>
                </div>
                <div class="info-item">
                    <span class="info-icono">🦉</span>
                    <div class="info-texto">
                        <p><strong>Powered by Didasko AI</strong></p>
                        <p class="mini">Predicciones inteligentes actualizadas cada día</p>
                    </div>
                </div>
            </div>
        `;
    }

    // HTML de ligas con banners
    let htmlLigas = '';
    if (dataLigas.success && dataLigas.ligas) {
        htmlLigas = `
            <div class="profeta-ligas">
                <div class="ligas-banners">
                    ${Object.entries(dataLigas.ligas).map(([key, liga]) => `
                        <div class="liga-banner-card" onclick="verLiga('${key}', '${liga.nombre.replace(/'/g, "\\'")}', '${liga.banner}')">
                            <div class="liga-banner-img">
                                <img src="${liga.banner}" alt="${liga.nombre}" onerror="this.style.display='none'; this.parentElement.classList.add('sin-imagen');">
                            </div>
                            <div class="liga-banner-info">
                                <h4>${liga.nombre}</h4>
                                <p>${liga.pais}</p>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    contenedor.innerHTML = `
        <div class="profeta-header">
            <h2>🌐 Profeta Deportivo</h2>
            <p class="profeta-fecha">📅 ${fecha}</p>
        </div>
        
        ${htmlPartidosHoy}
        ${htmlLigas}
    `;
}

// ===================================
// 🌐 Renderizar UN partido
// ===================================
function renderizarPartido(partido) {
    const escudoLocal = partido.strHomeTeamBadge || 'assets/logo/buho-mascota.png';
    const escudoVisita = partido.strAwayTeamBadge || 'assets/logo/buho-mascota.png';
    const hora = partido.strTime ? partido.strTime.substring(0, 5) : '--:--';
    const estado = partido.strStatus === 'FT' ? '✅ Finalizado' : '🕒 Programado';
    
    let resultado = '';
    if (partido.intHomeScore !== null && partido.intAwayScore !== null) {
        resultado = `
            <div class="partido-resultado">
                <span class="resultado-marcador">${partido.intHomeScore} - ${partido.intAwayScore}</span>
            </div>
        `;
    } else {
        resultado = `<div class="partido-hora">🕒 ${hora}</div>`;
    }

    return `
        <div class="partido-card" onclick="verDetallePartido('${partido.idEvent}')">
            <div class="partido-liga">🏆 ${partido.strLeague || 'Liga'}</div>
            <div class="partido-equipos">
                <div class="equipo local">
                    <img src="${escudoLocal}" alt="${partido.strHomeTeam}" onerror="this.src='assets/logo/buho-mascota.png'">
                    <p>${partido.strHomeTeam}</p>
                </div>
                ${resultado}
                <div class="equipo visitante">
                    <img src="${escudoVisita}" alt="${partido.strAwayTeam}" onerror="this.src='assets/logo/buho-mascota.png'">
                    <p>${partido.strAwayTeam}</p>
                </div>
            </div>
            <div class="partido-info-extra">
                <span class="partido-estado">${estado}</span>
                ${partido.strVenue ? `<span class="partido-lugar">📍 ${partido.strVenue}</span>` : ''}
            </div>
        </div>
    `;
}

// ===================================
// 🏆 Ver partidos de una liga
// ===================================
async function verLiga(ligaKey, ligaNombre, ligaBanner) {
    const contenedor = document.getElementById('profeta-resultado');
    ligaSeleccionada = ligaKey;

    contenedor.innerHTML = `
        <div class="profeta-loader">
            <span class="loader"></span>
            <p>🦉 Cargando ${ligaNombre}...</p>
        </div>
    `;

    try {
        const [pasadosRes, proximosRes] = await Promise.all([
            fetch(`/api/profeta/liga/${ligaKey}/pasados`, { credentials: 'include' }),
            fetch(`/api/profeta/liga/${ligaKey}/proximos`, { credentials: 'include' })
        ]);

        const pasados = await pasadosRes.json();
        const proximos = await proximosRes.json();

        renderizarLigaCompleta(ligaNombre, ligaBanner, pasados, proximos);
    } catch (error) {
        contenedor.innerHTML = `
            <div class="mensaje-error">❌ Error: ${error.message}</div>
            <button onclick="volverAProfeta()" class="btn-otra">🔙 Volver</button>
        `;
    }
}

// ===================================
// 🌐 Renderizar liga completa
// ===================================
function renderizarLigaCompleta(nombre, banner, pasados, proximos) {
    const contenedor = document.getElementById('profeta-resultado');

    let htmlProximos = '<p class="sub-mensaje">No hay próximos partidos</p>';
    if (proximos.success && proximos.partidos && proximos.partidos.length > 0) {
        htmlProximos = `
            <div class="partidos-lista">
                ${proximos.partidos.slice(0, 15).map(p => renderizarPartido(p)).join('')}
            </div>
        `;
    }

    let htmlPasados = '<p class="sub-mensaje">No hay partidos recientes</p>';
    if (pasados.success && pasados.partidos && pasados.partidos.length > 0) {
        htmlPasados = `
            <div class="partidos-lista">
                ${pasados.partidos.slice(0, 15).map(p => renderizarPartido(p)).join('')}
            </div>
        `;
    }

    contenedor.innerHTML = `
        <div class="liga-header-banner" style="background-image: url('${banner}');">
            <div class="liga-header-overlay">
                <button onclick="volverAProfeta()" class="btn-volver-liga">🔙 Volver</button>
                <h2>${nombre}</h2>
            </div>
        </div>
        
        <div class="liga-seccion">
            <h3 class="profeta-subtitulo">⏩ Próximos partidos</h3>
            ${htmlProximos}
        </div>
        
        <div class="liga-seccion">
            <h3 class="profeta-subtitulo">✅ Últimos resultados</h3>
            ${htmlPasados}
        </div>
    `;
}

// ===================================
// 🔍 Ver detalle de un partido
// ===================================
async function verDetallePartido(eventoId) {
    const contenedor = document.getElementById('profeta-resultado');

    contenedor.innerHTML = `
        <div class="profeta-loader">
            <span class="loader"></span>
            <p>🦉 Analizando el partido...</p>
        </div>
    `;

    try {
        const response = await fetch(`/api/profeta/partido/${eventoId}`, {
            credentials: 'include'
        });
        const data = await response.json();

        if (data.success && data.partido) {
            renderizarDetallePartido(data.partido);
        } else {
            throw new Error('No se pudo cargar el partido');
        }
    } catch (error) {
        contenedor.innerHTML = `
            <div class="mensaje-error">❌ Error: ${error.message}</div>
            <button onclick="volverAProfeta()" class="btn-otra">🔙 Volver</button>
        `;
    }
}

// ===================================
// 🌐 Renderizar detalle
// ===================================
function renderizarDetallePartido(p) {
    const contenedor = document.getElementById('profeta-resultado');

    const escudoLocal = p.strHomeTeamBadge || 'assets/logo/buho-mascota.png';
    const escudoVisita = p.strAwayTeamBadge || 'assets/logo/buho-mascota.png';
    const poster = p.strPoster || p.strThumb || p.strBanner;

    let resultado = '';
    if (p.intHomeScore !== null && p.intAwayScore !== null) {
        resultado = `<h1 class="marcador-grande">${p.intHomeScore} - ${p.intAwayScore}</h1>`;
    } else {
        resultado = `<h2 class="hora-grande">🕒 ${p.strTime ? p.strTime.substring(0,5) : '--:--'}</h2>`;
    }

    let videoHTML = '';
    if (p.strVideo) {
        const videoId = p.strVideo.match(/(?:v=|\/)([0-9A-Za-z_-]{11})/);
        if (videoId) {
            videoHTML = `
                <div class="partido-video">
                    <h3>📹 Highlights del partido</h3>
                    <iframe src="https://www.youtube.com/embed/${videoId[1]}"
                        frameborder="0" allowfullscreen></iframe>
                </div>
            `;
        }
    }

    contenedor.innerHTML = `
        <div class="detalle-header">
            <button onclick="volverAProfeta()" class="btn-volver-liga">🔙 Volver</button>
            <h2>🌐 Detalles del Partido</h2>
        </div>
        
        ${poster ? `<img src="${poster}" class="detalle-poster" alt="Poster">` : ''}
        
        <div class="detalle-partido">
            <div class="detalle-liga">🏆 ${p.strLeague}</div>
            
            <div class="detalle-equipos">
                <div class="detalle-equipo">
                    <img src="${escudoLocal}" alt="${p.strHomeTeam}">
                    <h3>${p.strHomeTeam}</h3>
                </div>
                
                <div class="detalle-vs">
                    ${resultado}
                    <p class="detalle-fecha">📅 ${p.dateEvent}</p>
                </div>
                
                <div class="detalle-equipo">
                    <img src="${escudoVisita}" alt="${p.strAwayTeam}">
                    <h3>${p.strAwayTeam}</h3>
                </div>
            </div>
            
            <div class="detalle-info">
                ${p.strVenue ? `<p>📍 <strong>Estadio:</strong> ${p.strVenue}</p>` : ''}
                ${p.strCountry ? `<p>🌍 <strong>País:</strong> ${p.strCountry}</p>` : ''}
                ${p.strSeason ? `<p>📅 <strong>Temporada:</strong> ${p.strSeason}</p>` : ''}
                ${p.strStatus ? `<p>⚽ <strong>Estado:</strong> ${p.strStatus === 'FT' ? 'Finalizado' : p.strStatus}</p>` : ''}
            </div>
            
            <!-- 🔮 BOTÓN DE PREDICCIÓN IA -->
            <div class="prediccion-boton-container">
                <button onclick="verPrediccionIA('${p.idEvent}')" class="btn-prediccion-ia">
                    🔮 Ver Predicción con IA
                </button>
                <p class="prediccion-hint">🤖 Análisis inteligente powered by NVIDIA</p>
            </div>
            
            <!-- Aquí aparecerá la predicción -->
            <div id="prediccion-resultado"></div>
            
            ${videoHTML}
        </div>
    `;
}

// ===================================
// 🔮 VER PREDICCIÓN IA
// ===================================
async function verPrediccionIA(eventoId) {
    const contenedor = document.getElementById('prediccion-resultado');
    const boton = document.querySelector('.btn-prediccion-ia');
    
    if (!contenedor) return;
    
    // Deshabilitar botón
    if (boton) {
        boton.disabled = true;
        boton.innerHTML = '⏳ Analizando...';
    }
    
    contenedor.innerHTML = `
        <div class="prediccion-loader">
            <span class="loader"></span>
            <p>🦉 El Profeta está analizando el partido...</p>
            <p class="mini">Consultando datos históricos y forma reciente</p>
        </div>
    `;
    
    try {
        const response = await fetch(`/api/profeta/predecir/${eventoId}`, {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        // Si requiere login
        if (data.requiere_login) {
            contenedor.innerHTML = `
                <div class="prediccion-error">
                    <h3>🔒 Debes iniciar sesión</h3>
                    <p>Para ver predicciones IA necesitas estar registrado</p>
                    <button onclick="window.location.href='login.html'" class="btn-otra">Iniciar sesión</button>
                </div>
            `;
            if (boton) {
                boton.disabled = false;
                boton.innerHTML = '🔮 Ver Predicción con IA';
            }
            return;
        }
        
        // Si excede el límite (no VIP)
        if (data.requiere_vip) {
            contenedor.innerHTML = `
                <div class="prediccion-vip">
                    <div class="vip-icono">💎</div>
                    <h3>🔒 Límite diario alcanzado</h3>
                    <p class="vip-mensaje">${data.mensaje}</p>
                    
                    <div class="vip-beneficios">
                        <h4>✨ Beneficios VIP:</h4>
                        <ul>
                            <li>🔮 Predicciones ILIMITADAS por 30 días</li>
                            <li>⚽ Todos los partidos de las 10 ligas</li>
                            <li>📊 Análisis detallado con IA</li>
                            <li>🎯 Acceso prioritario a nuevas funciones</li>
                        </ul>
                    </div>
                    
                    <div class="vip-precio">
                        <h4>💰 Donación voluntaria</h4>
                        <p class="precio-monto">${data.precio}</p>
                        <p class="precio-metodo">${data.metodo}</p>
                    </div>
                    
                 <div class="vip-acciones">
                        <button onclick="contactarWhatsAppVIP()" class="btn-vip-donar">
                            💛 Contactar y Donar
                        </button>
                        <button onclick="mostrarActivarVIP()" class="btn-vip-codigo">
                            🎟️ Ya tengo código VIP
                        </button>
                    </div>
                    
                    <p class="vip-nota">
                        📱 <strong>WhatsApp directo:</strong> 
                        <a href="https://wa.me/573171547065?text=${encodeURIComponent('Hola Profeta! 🦉 Vengo de Didasko AI y quiero mi código VIP. Ya donaré ⚽')}" target="_blank">+57 317 154 7065</a>
                    </p>
                </div>
            `;
            if (boton) {
                boton.style.display = 'none';
            }
            return;
        }
        
        // Si hay error
        if (!data.success) {
            contenedor.innerHTML = `
                <div class="prediccion-error">
                    ❌ ${data.error || 'Error generando predicción'}
                </div>
            `;
            if (boton) {
                boton.disabled = false;
                boton.innerHTML = '🔮 Ver Predicción con IA';
            }
            return;
        }
        
        // ✅ Mostrar predicción exitosa
        const badgeVIP = data.es_vip ? '<span class="badge-vip">💎 VIP</span>' : '';
        const badgeCache = data.desde_cache ? '<span class="badge-cache">💾 Cache</span>' : '<span class="badge-nueva">🆕 Nueva</span>';
        
        contenedor.innerHTML = `
            <div class="prediccion-exitosa">
                <div class="prediccion-header">
                    <h3>🔮 Predicción del Profeta</h3>
                    <div class="prediccion-badges">
                        ${badgeVIP}
                        ${badgeCache}
                    </div>
                </div>
                
                <div class="prediccion-texto">
                    ${formatearPrediccion(data.prediccion)}
                </div>
                
                <div class="prediccion-footer">
                    <p class="prediccion-ia">🤖 Generado con <strong>${data.ia_usada.toUpperCase()}</strong></p>
                    <p class="prediccion-disclaimer">⚠️ Predicción con IA para entretenimiento. No es garantía.</p>
                </div>
            </div>
        `;
        
        // Ocultar botón después de mostrar
        if (boton) {
            boton.style.display = 'none';
        }
        
    } catch (error) {
        contenedor.innerHTML = `
            <div class="prediccion-error">
                ❌ Error de conexión: ${error.message}
            </div>
        `;
        if (boton) {
            boton.disabled = false;
            boton.innerHTML = '🔮 Ver Predicción con IA';
        }
    }
}

// ===================================
// 🎨 Formatear texto de predicción
// ===================================
function formatearPrediccion(texto) {
    if (!texto) return '';
    
    // Convertir markdown básico a HTML
    let html = texto
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
    
    return `<p>${html}</p>`;
}

// ===================================
// 🎟️ Modal activar código VIP
// ===================================
function mostrarActivarVIP() {
    const codigo = prompt('🎟️ Ingresa tu código VIP:\n\n(Ejemplo: DIDASKO-ABC123)');
    
    if (!codigo || !codigo.trim()) return;
    
    activarCodigoVIP(codigo.trim().toUpperCase());
}

async function activarCodigoVIP(codigo) {
    try {
        const response = await fetch('/api/profeta/vip/activar', {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ codigo })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(`🎉 ${data.mensaje}\n\nVIP activo hasta: ${new Date(data.vip_hasta).toLocaleDateString('es-CO')}`);
            location.reload();
        } else {
            alert(`❌ ${data.error}`);
        }
    } catch (error) {
        alert(`❌ Error: ${error.message}`);
    }
}

// ===================================
// 🔙 Volver al Profeta principal
// ===================================
function volverAProfeta() {
    profetaCargado = false;
    ligaSeleccionada = null;
    mostrarPartidosHoy();
    profetaCargado = true;
}

// ===================================
// 📱 Contactar WhatsApp para VIP
// ===================================
function contactarWhatsAppVIP() {
    const mensaje = encodeURIComponent(
        'Hola Profeta! 🦉 Vengo de Didasko AI y quiero mi código VIP. Ya donaré ⚽'
    );
    const numero = '573171547065';
    const url = `https://wa.me/${numero}?text=${mensaje}`;
    window.open(url, '_blank');
}

if (CONFIG.DEBUG) console.log('🌐 profeta.js V3.3 cargado con Predicciones IA + WhatsApp');
