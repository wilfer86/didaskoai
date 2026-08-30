// profeta.js - Didasko AI V4.1
let profetaCargado = false;

function convertirHoraColombia(horaUTC, fechaUTC) {
    if (!horaUTC) return '--:--';
    try {
        const horaLimpia = horaUTC.substring(0, 5);
        const fechaHoraUTC = new Date(`${fechaUTC}T${horaLimpia}:00Z`);
        return fechaHoraUTC.toLocaleTimeString('es-CO', {
            timeZone: 'America/Bogota',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });
    } catch (e) {
        return horaUTC.substring(0, 5);
    }
}

async function cargarProfeta() {
    if (profetaCargado) return;
    await mostrarPartidosHoy();
    profetaCargado = true;
}

async function mostrarPartidosHoy() {
    const contenedor = document.getElementById('profeta-resultado');
    if (!contenedor) return;

    contenedor.innerHTML = '<div class="profeta-loader"><span class="loader"></span><p>🦉 Cargando partidos...</p></div>';

    try {
        const [partidosRes, ligasRes] = await Promise.all([
            fetch('/api/profeta/hoy', { credentials: 'include' }),
            fetch('/api/profeta/ligas', { credentials: 'include' })
        ]);

        const data = await partidosRes.json();
        const ligasData = await ligasRes.json();

        renderizarProfeta(data, ligasData);
    } catch (error) {
        contenedor.innerHTML = `<div class="mensaje-error"> Error: ${error.message}</div>`;
    }
}

function renderizarProfeta(dataPartidos, dataLigas) {
    const contenedor = document.getElementById('profeta-resultado');
    if (!contenedor) return;

    const fecha = new Date().toLocaleDateString('es-CO', {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    });

    let htmlPartidos = '';
    if (dataPartidos.success && dataPartidos.partidos && dataPartidos.partidos.length > 0) {
        htmlPartidos = `
            <div class="profeta-partidos-hoy">
                <h3 class="profeta-subtitulo">🏆 Partidos</h3>
                <div class="partidos-lista">
                    ${dataPartidos.partidos.map(p => renderizarPartido(p)).join('')}
                </div>
            </div>
        `;
    } else {
        htmlPartidos = `
            <div class="profeta-info-banner">
                <div class="info-item">
                    <span class="info-icono">📅</span>
                    <div class="info-texto">
                        <p><strong>No hay partidos hoy</strong></p>
                        <p class="mini">Selecciona una liga abajo</p>
                    </div>
                </div>
            </div>
        `;
    }

    let htmlLigas = '';
    if (dataLigas.success && dataLigas.ligas) {
        htmlLigas = `
            <div class="profeta-ligas">
                <div class="ligas-banners">
                    ${Object.entries(dataLigas.ligas).map(([key, liga]) => `
                        <div class="liga-banner-card" onclick="verLiga('${key}', '${liga.nombre}', '${liga.banner}')">
                            <div class="liga-banner-img">
                                <img src="${liga.banner}" alt="${liga.nombre}" onerror="this.style.display='none'">
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
        ${htmlPartidos}
        ${htmlLigas}
    `;
}

function renderizarPartido(partido) {
    // Obtener nombres reales de equipos
    const nombreLocal = partido.strHomeTeam && partido.strHomeTeam !== 'Local' 
        ? partido.strHomeTeam 
        : 'Equipo Local';
    
    const nombreVisitante = partido.strAwayTeam && partido.strAwayTeam !== 'Visitante' 
        ? partido.strAwayTeam 
        : 'Equipo Visitante';
    
    // Obtener escudos reales
    const escudoLocal = (partido.strHomeTeamBadge && partido.strHomeTeamBadge.startsWith('http')) 
        ? partido.strHomeTeamBadge 
        : 'assets/logo/buho-mascota.png';
    
    const escudoVisitante = (partido.strAwayTeamBadge && partido.strAwayTeamBadge.startsWith('http')) 
        ? partido.strAwayTeamBadge 
        : 'assets/logo/buho-mascota.png';
    
    // Convertir hora
    const horaColombia = convertirHoraColombia(partido.strTime, partido.dateEvent);
    
    // Determinar estado
    const estado = partido.strStatus === 'FT' ? '✅ Finalizado' : 
                   (partido.strStatus === 'LIVE' ? '🔴 EN VIVO' : `🕒 ${horaColombia}`);
    
    // Marcador o hora
    let resultado = '';
    if (partido.intHomeScore !== null && partido.intAwayScore !== null && partido.strStatus === 'FT') {
        resultado = `<div class="partido-resultado"><span class="resultado-marcador">${partido.intHomeScore} - ${partido.intAwayScore}</span></div>`;
    } else if (partido.strStatus === 'LIVE' && partido.intHomeScore !== null) {
        resultado = `<div class="partido-resultado"><span class="resultado-marcador">${partido.intHomeScore} - ${partido.intAwayScore || 0}</span></div>`;
    } else {
        resultado = `<div class="partido-hora">🕒 ${horaColombia}</div>`;
    }

    return `
        <div class="partido-card" onclick="verDetallePartido('${partido.idEvent}')">
            <div class="partido-liga">🏆 ${partido.strLeague || 'Liga'}</div>
            <div class="partido-equipos">
                <div class="equipo local">
                    <img src="${escudoLocal}" alt="${nombreLocal}" onerror="this.src='assets/logo/buho-mascota.png'">
                    <p>${nombreLocal}</p>
                </div>
                ${resultado}
                <div class="equipo visitante">
                    <img src="${escudoVisitante}" alt="${nombreVisitante}" onerror="this.src='assets/logo/buho-mascota.png'">
                    <p>${nombreVisitante}</p>
                </div>
            </div>
            <div class="partido-info-extra">
                <span class="partido-estado">${estado}</span>
                ${partido.strVenue ? `<span class="partido-lugar">📍 ${partido.strVenue}</span>` : ''}
            </div>
        </div>
    `;
}

async function verLiga(ligaKey, ligaNombre, ligaBanner) {
    const contenedor = document.getElementById('profeta-resultado');
    contenedor.innerHTML = `<div class="profeta-loader"><span class="loader"></span><p>🦉 Cargando ${ligaNombre}...</p></div>`;

    try {
        const [pasadosRes, proximosRes] = await Promise.all([
            fetch(`/api/profeta/liga/${ligaKey}/pasados`, { credentials: 'include' }),
            fetch(`/api/profeta/liga/${ligaKey}/proximos`, { credentials: 'include' })
        ]);

        const pasados = await pasadosRes.json();
        const proximos = await proximosRes.json();

        renderizarLigaCompleta(ligaNombre, ligaBanner, pasados, proximos);
    } catch (error) {
        contenedor.innerHTML = `<div class="mensaje-error">❌ Error: ${error.message}</div>`;
    }
}

function renderizarLigaCompleta(nombre, banner, pasados, proximos) {
    const contenedor = document.getElementById('profeta-resultado');

    const htmlProximos = proximos.success && proximos.partidos && proximos.partidos.length > 0
        ? `<div class="partidos-lista">${proximos.partidos.slice(0, 15).map(p => renderizarPartido(p)).join('')}</div>`
        : '<p class="sub-mensaje">No hay próximos partidos</p>';

    const htmlPasados = pasados.success && pasados.partidos && pasados.partidos.length > 0
        ? `<div class="partidos-lista">${pasados.partidos.slice(0, 15).map(p => renderizarPartido(p)).join('')}</div>`
        : '<p class="sub-mensaje">No hay resultados recientes</p>';

    contenedor.innerHTML = `
        <div class="liga-header-banner" style="background-image: url('${banner}');">
            <div class="liga-header-overlay">
                <button onclick="volverAProfeta()" class="btn-volver-liga">🔙 Volver</button>
                <h2>${nombre}</h2>
            </div>
        </div>
        <div class="liga-seccion">
            <h3 class="profeta-subtitulo">⏩ Próximos</h3>
            ${htmlProximos}
        </div>
        <div class="liga-seccion">
            <h3 class="profeta-subtitulo">✅ Resultados</h3>
            ${htmlPasados}
        </div>
    `;
}

async function verDetallePartido(eventoId) {
    const contenedor = document.getElementById('profeta-resultado');
    contenedor.innerHTML = '<div class="profeta-loader"><span class="loader"></span><p>🦉 Cargando...</p></div>';

    try {
        const response = await fetch(`/api/profeta/partido/${eventoId}`, { credentials: 'include' });
        const data = await response.json();

        if (data.success && data.partido) {
            renderizarDetallePartido(data.partido);
        } else {
            throw new Error('No se pudo cargar');
        }
    } catch (error) {
        contenedor.innerHTML = `<div class="mensaje-error">❌ Error: ${error.message}</div><button onclick="volverAProfeta()" class="btn-otra">🔙 Volver</button>`;
    }
}

function renderizarDetallePartido(p) {
    const contenedor = document.getElementById('profeta-resultado');
    const horaColombia = convertirHoraColombia(p.strTime, p.dateEvent);
    const partidoFinalizado = p.strStatus === 'FT';

    let resultado = '';
    if (p.intHomeScore !== null && p.intAwayScore !== null) {
        resultado = `<h1 class="marcador-grande">${p.intHomeScore} - ${p.intAwayScore}</h1>`;
    } else {
        resultado = `<h2 class="hora-grande"> ${horaColombia}</h2>`;
    }

    const accionHTML = partidoFinalizado
        ? `<button onclick="verPrediccionPasada('${p.idEvent}')" class="btn-prediccion-ia">🔍 Ver predicción pasada</button>`
        : `<button onclick="verPrediccionIA('${p.idEvent}')" class="btn-prediccion-ia">🔮 Ver Predicción IA</button>`;

    contenedor.innerHTML = `
        <div class="detalle-header">
            <button onclick="volverAProfeta()" class="btn-volver-liga">🔙 Volver</button>
            <h2> Detalles</h2>
        </div>
        <div class="detalle-partido">
            <div class="detalle-liga">🏆 ${p.strLeague}</div>
            <div class="detalle-equipos">
                <div class="detalle-equipo"><h3>${p.strHomeTeam || 'Local'}</h3></div>
                <div class="detalle-vs">${resultado}</div>
                <div class="detalle-equipo"><h3>${p.strAwayTeam || 'Visitante'}</h3></div>
            </div>
            <div class="detalle-info">
                ${p.strVenue ? `<p>📍 ${p.strVenue}</p>` : ''}
                <p>📅 ${p.dateEvent}</p>
            </div>
            ${accionHTML}
            <div id="prediccion-resultado"></div>
        </div>
    `;
}

async function verPrediccionIA(eventoId) {
    const contenedor = document.getElementById('prediccion-resultado');
    contenedor.innerHTML = '<div class="prediccion-loader"><span class="loader"></span><p> Analizando...</p></div>';

    try {
        const response = await fetch(`/api/profeta/predecir/${eventoId}`, { credentials: 'include' });
        const data = await response.json();

        if (data.requiere_login) {
            contenedor.innerHTML = '<div class="prediccion-error"><h3>🔒 Inicia sesión</h3><button onclick="window.location.href=\'login.html\'">Iniciar sesión</button></div>';
            return;
        }

        if (data.requiere_vip) {
            contenedor.innerHTML = `
                <div class="prediccion-vip">
                    <h3>🔒 Límite alcanzado</h3>
                    <p>${data.mensaje}</p>
                    <p class="vip-nota">📱 <a href="https://wa.me/573171547065" target="_blank">WhatsApp: +57 317 154 7065</a></p>
                </div>
            `;
            return;
        }

        if (!data.success) {
            contenedor.innerHTML = `<div class="prediccion-error"> ${data.error}</div>`;
            return;
        }

        contenedor.innerHTML = `
            <div class="prediccion-exitosa">
                <h3>🔮 Predicción</h3>
                <div class="prediccion-texto">${formatearPrediccion(data.prediccion)}</div>
                <p class="prediccion-ia">🤖 IA: ${data.ia_usada}</p>
            </div>
        `;
    } catch (error) {
        contenedor.innerHTML = `<div class="prediccion-error">❌ Error: ${error.message}</div>`;
    }
}

async function verPrediccionPasada(eventoId) {
    const contenedor = document.getElementById('prediccion-resultado');
    contenedor.innerHTML = '<div class="prediccion-loader"><span class="loader"></span><p> Cargando...</p></div>';

    try {
        const response = await fetch(`/api/profeta/predecir/${eventoId}`, { credentials: 'include' });
        const data = await response.json();

        if (data.success && data.prediccion) {
            contenedor.innerHTML = `
                <div class="prediccion-exitosa">
                    <h3>🔍 Predicción pasada</h3>
                    <div class="prediccion-texto">${formatearPrediccion(data.prediccion)}</div>
                </div>
            `;
        } else {
            contenedor.innerHTML = '<div class="prediccion-error">❌ No hay predicción</div>';
        }
    } catch (error) {
        contenedor.innerHTML = `<div class="prediccion-error">❌ Error: ${error.message}</div>`;
    }
}

function formatearPrediccion(texto) {
    if (!texto) return '';
    return texto
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
}

function volverAProfeta() {
    profetaCargado = false;
    mostrarPartidosHoy();
    profetaCargado = true;
}

console.log('✅ profeta.js V4.1 cargado');
