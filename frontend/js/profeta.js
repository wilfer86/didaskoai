// ==========================================
// profeta.js - Didasko AI V3.2
// Profeta Deportivo ⚽
// ==========================================

let ligaSeleccionada = null;
let profetaCargado = false;

// ==========================================
// 🔄 Cargar Profeta al abrir sección
// ==========================================
async function cargarProfeta() {
    if (profetaCargado) return;
    
    mostrarPartidosHoy();
    profetaCargado = true;
}

// ==========================================
// ⚽ Mostrar partidos del día
// ==========================================
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
        // Obtener partidos del día
        const response = await fetch('/api/profeta/hoy', {
            credentials: 'include'
        });
        const data = await response.json();
        
        // Obtener ligas también
        const ligasRes = await fetch('/api/profeta/ligas', { credentials: 'include' });
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

// ==========================================
// 🎨 Renderizar Profeta con partidos + ligas
// ==========================================
function renderizarProfeta(dataPartidos, dataLigas) {
    const contenedor = document.getElementById('profeta-resultado');
    if (!contenedor) return;
    
    const fecha = new Date().toLocaleDateString('es-CO', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    
    // HTML de ligas (grid)
    let htmlLigas = '';
    if (dataLigas.success && dataLigas.ligas) {
        htmlLigas = `
            <div class="profeta-ligas">
                <h3 class="profeta-subtitulo">🏆 Selecciona una liga</h3>
                <div class="ligas-grid">
                    ${Object.entries(dataLigas.ligas).map(([key, liga]) => `
                        <button class="liga-card" onclick="verLiga('${key}', '${liga.nombre}', '${liga.emoji}')">
                            <span class="liga-emoji">${liga.emoji}</span>
                            <span class="liga-nombre">${liga.nombre}</span>
                            <span class="liga-pais">${liga.pais}</span>
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // HTML de partidos de hoy
    let htmlPartidos = '';
    if (dataPartidos.success) {
        if (dataPartidos.partidos && dataPartidos.partidos.length > 0) {
            htmlPartidos = `
                <div class="profeta-partidos">
                    <h3 class="profeta-subtitulo">📅 Partidos importantes de hoy</h3>
                    <div class="partidos-lista">
                        ${dataPartidos.partidos.map(p => renderizarPartido(p)).join('')}
                    </div>
                </div>
            `;
        } else {
            htmlPartidos = `
                <div class="profeta-sin-partidos">
                    <p>📅 <strong>No hay partidos de ligas prioritarias hoy</strong></p>
                    <p class="sub-mensaje">Selecciona una liga arriba para ver partidos pasados o próximos</p>
                </div>
            `;
        }
    }
    
    // Renderizar todo
    contenedor.innerHTML = `
        <div class="profeta-header">
            <h2>⚽ Profeta Deportivo</h2>
            <p class="profeta-fecha">🗓️ ${fecha}</p>
        </div>
        
        ${htmlLigas}
        ${htmlPartidos}
        
        <div class="profeta-info-final">
            <p>🦉 <strong>Powered by Didasko AI</strong></p>
            <p class="mini">Predicciones inteligentes actualizadas cada día</p>
        </div>
    `;
}

// ==========================================
// 🎨 Renderizar UN partido individual
// ==========================================
function renderizarPartido(partido) {
    const escudoLocal = partido.strHomeTeamBadge || partido.strThumb || 'assets/logo/buho-mascota.png';
    const escudoVisita = partido.strAwayTeamBadge || 'assets/logo/buho-mascota.png';
    const hora = partido.strTime ? partido.strTime.substring(0, 5) : '--:--';
    const estado = partido.strStatus === 'FT' ? '✅ Finalizado' : '⏰ Programado';
    
    let resultado = '';
    if (partido.intHomeScore !== null && partido.intAwayScore !== null) {
        resultado = `
            <div class="partido-resultado">
                <span class="resultado-marcador">${partido.intHomeScore} - ${partido.intAwayScore}</span>
            </div>
        `;
    } else {
        resultado = `<div class="partido-hora">⏰ ${hora}</div>`;
    }
    
    return `
        <div class="partido-card" onclick="verDetallePartido('${partido.idEvent}')">
            <div class="partido-liga">
                🏆 ${partido.strLeague || 'Liga'}
            </div>
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

// ==========================================
// 🏆 Ver partidos de una liga
// ==========================================
async function verLiga(ligaKey, ligaNombre, ligaEmoji) {
    const contenedor = document.getElementById('profeta-resultado');
    ligaSeleccionada = ligaKey;
    
    contenedor.innerHTML = `
        <div class="profeta-loader">
            <span class="loader"></span>
            <p>🦉 Cargando ${ligaEmoji} ${ligaNombre}...</p>
        </div>
    `;
    
    try {
        // Obtener partidos pasados y próximos en paralelo
        const [pasadosRes, proximosRes] = await Promise.all([
            fetch(`/api/profeta/liga/${ligaKey}/pasados`, { credentials: 'include' }),
            fetch(`/api/profeta/liga/${ligaKey}/proximos`, { credentials: 'include' })
        ]);
        
        const pasados = await pasadosRes.json();
        const proximos = await proximosRes.json();
        
        renderizarLigaCompleta(ligaNombre, ligaEmoji, pasados, proximos);
    } catch (error) {
        contenedor.innerHTML = `
            <div class="mensaje-error">
                ❌ Error cargando liga: ${error.message}
            </div>
            <button onclick="volverAProfeta()" class="btn-otra">🔙 Volver</button>
        `;
    }
}

// ==========================================
// 🎨 Renderizar liga completa
// ==========================================
function renderizarLigaCompleta(nombre, emoji, pasados, proximos) {
    const contenedor = document.getElementById('profeta-resultado');
    
    let htmlProximos = '<p class="sub-mensaje">No hay próximos partidos programados</p>';
    if (proximos.success && proximos.partidos && proximos.partidos.length > 0) {
        htmlProximos = `
            <div class="partidos-lista">
                ${proximos.partidos.slice(0, 10).map(p => renderizarPartido(p)).join('')}
            </div>
        `;
    }
    
    let htmlPasados = '<p class="sub-mensaje">No hay partidos recientes</p>';
    if (pasados.success && pasados.partidos && pasados.partidos.length > 0) {
        htmlPasados = `
            <div class="partidos-lista">
                ${pasados.partidos.slice(0, 10).map(p => renderizarPartido(p)).join('')}
            </div>
        `;
    }
    
    contenedor.innerHTML = `
        <div class="liga-header">
            <button onclick="volverAProfeta()" class="btn-volver-liga">🔙 Volver</button>
            <h2>${emoji} ${nombre}</h2>
        </div>
        
        <div class="liga-seccion">
            <h3 class="profeta-subtitulo">⏭️ Próximos partidos</h3>
            ${htmlProximos}
        </div>
        
        <div class="liga-seccion">
            <h3 class="profeta-subtitulo">✅ Últimos resultados</h3>
            ${htmlPasados}
        </div>
    `;
}

// ==========================================
// 🔍 Ver detalle de un partido
// ==========================================
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
            <div class="mensaje-error">
                ❌ Error: ${error.message}
            </div>
            <button onclick="volverAProfeta()" class="btn-otra">🔙 Volver</button>
        `;
    }
}

// ==========================================
// 🎨 Renderizar detalle de partido
// ==========================================
function renderizarDetallePartido(p) {
    const contenedor = document.getElementById('profeta-resultado');
    
    const escudoLocal = p.strHomeTeamBadge || 'assets/logo/buho-mascota.png';
    const escudoVisita = p.strAwayTeamBadge || 'assets/logo/buho-mascota.png';
    const poster = p.strPoster || p.strThumb || p.strBanner;
    
    let resultado = '';
    if (p.intHomeScore !== null && p.intAwayScore !== null) {
        resultado = `<h1 class="marcador-grande">${p.intHomeScore} - ${p.intAwayScore}</h1>`;
    } else {
        resultado = `<h2 class="hora-grande">⏰ ${p.strTime ? p.strTime.substring(0,5) : '--:--'}</h2>`;
    }
    
    let videoHTML = '';
    if (p.strVideo) {
        const videoId = p.strVideo.match(/(?:v=|\/)([0-9A-Za-z_-]{11})/);
        if (videoId) {
            videoHTML = `
                <div class="partido-video">
                    <h3>🎬 Highlights del partido</h3>
                    <iframe src="https://www.youtube.com/embed/${videoId[1]}" 
                        frameborder="0" allowfullscreen></iframe>
                </div>
            `;
        }
    }
    
    contenedor.innerHTML = `
        <div class="detalle-header">
            <button onclick="volverAProfeta()" class="btn-volver-liga">🔙 Volver</button>
            <h2>⚽ Detalles del Partido</h2>
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
                ${p.strSeason ? `<p>📆 <strong>Temporada:</strong> ${p.strSeason}</p>` : ''}
                ${p.strStatus ? `<p>⏱️ <strong>Estado:</strong> ${p.strStatus === 'FT' ? 'Finalizado' : p.strStatus}</p>` : ''}
            </div>
            
            ${videoHTML}
        </div>
    `;
}

// ==========================================
// 🔙 Volver al Profeta principal
// ==========================================
function volverAProfeta() {
    profetaCargado = false;
    ligaSeleccionada = null;
    mostrarPartidosHoy();
    profetaCargado = true;
}

if (CONFIG.DEBUG) console.log('⚽ profeta.js V1.0 cargado');
