function renderizarPartido(partido) {
    const escudoLocal = partido.strHomeTeamBadge || 'assets/logo/buho-mascota.png';
    const escudoVisita = partido.strAwayTeamBadge || 'assets/logo/buho-mascota.png';
    
    const fechaPartido = partido.dateEvent;
    const horaUTC = partido.strTime;
    
    let horaColombia = '--:--';
    if (fechaPartido && horaUTC) {
        try {
            const horaLimpia = horaUTC.substring(0, 5);
            const fechaHoraUTC = new Date(`${fechaPartido}T${horaLimpia}:00Z`);
            horaColombia = fechaHoraUTC.toLocaleTimeString('es-CO', {
                timeZone: 'America/Bogota',
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            });
        } catch (e) {
            horaColombia = horaUTC.substring(0, 5);
        }
    }
    
    const estado = partido.strStatus === 'FT' ? '✅ Finalizado' : (partido.strStatus === 'LIVE' ? '🔴 EN VIVO' : `🕒 ${horaColombia}`);
    
    let resultado = '';
    if (partido.intHomeScore !== null && partido.intAwayScore !== null && partido.strStatus === 'FT') {
        resultado = `
            <div class="partido-resultado">
                <span class="resultado-marcador">${partido.intHomeScore} - ${partido.intAwayScore}</span>
            </div>
        `;
    } else if (partido.strStatus === 'LIVE') {
        resultado = `
            <div class="partido-resultado">
                <span class="resultado-marcador">${partido.intHomeScore || 0} - ${partido.intAwayScore || 0}</span>
            </div>
        `;
    } else {
        resultado = `<div class="partido-hora">🕒 ${horaColombia}</div>`;
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
