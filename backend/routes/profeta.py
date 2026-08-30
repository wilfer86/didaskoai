# ===================================
# profeta.py - Profeta Deportivo V4.0
# ESPN API (Colombia) + TheSportsDB (Internacional)
# ===================================

import os
import requests
import pytz
import re
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session
from supabase_client import get_client

profeta_bp = Blueprint('profeta', __name__)

# CONFIGURACIÓN
THESPORTSDB_KEY = os.getenv('THESPORTSDB_KEY', '123')
THESPORTSDB_URL = f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_KEY}"
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent"

# ESPN API - Fútbol Colombiano (GRATIS, sin registro)
ESPN_COLOMBIA_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/col.1/scoreboard"
ESPN_COPA_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/col.cup/scoreboard"

LIGAS_PRIORITARIAS = {
    'colombia_primera': {'id': 4497, 'nombre': 'Liga BetPlay Dimayor', 'pais': 'Colombia', 'banner': 'assets/fondos/colombia-primera.jpeg'},
    'copa_colombia': {'id': 5183, 'nombre': 'Copa BetPlay', 'pais': 'Colombia', 'banner': 'assets/fondos/copa-colombia.jpeg'},
    'champions': {'id': 4480, 'nombre': 'UEFA Champions League', 'pais': 'Europa', 'banner': 'assets/fondos/champions.jpeg'},
    'libertadores': {'id': 4482, 'nombre': 'Copa Libertadores', 'pais': 'Sudamérica', 'banner': 'assets/fondos/libertadores.jpeg'},
    'premier': {'id': 4328, 'nombre': 'Premier League', 'pais': 'Inglaterra', 'banner': 'assets/fondos/premier.jpeg'},
    'laliga': {'id': 4335, 'nombre': 'LaLiga', 'pais': 'España', 'banner': 'assets/fondos/laliga.jpeg'},
    'bundesliga': {'id': 4331, 'nombre': 'Bundesliga', 'pais': 'Alemania', 'banner': 'assets/fondos/bundesliga.jpeg'},
    'serie_a': {'id': 4332, 'nombre': 'Serie A', 'pais': 'Italia', 'banner': 'assets/fondos/serie-a.jpeg'},
}

def obtener_email_sesion():
    return session.get('usuario_email')

def obtener_fecha_hoy_bogota():
    tz_bogota = pytz.timezone('America/Bogota')
    return datetime.now(tz_bogota).strftime('%Y-%m-%d')

def obtener_partidos_espn_colombia():
    """Obtiene partidos de la Liga BetPlay desde ESPN"""
    partidos = []
    try:
        response = requests.get(ESPN_COLOMBIA_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            eventos = data.get('events', [])
            for evento in eventos:
                try:
                    competencia = evento.get('competitions', [{}])[0]
                    competidores = competencia.get('competitors', [])
                    local = competidores[0] if len(competidores) > 0 else {}
                    visitante = competidores[1] if len(competidores) > 1 else {}
                    
                    estado_tipo = evento.get('status', {}).get('type', {}).get('state', '')
                    fecha_utc = evento.get('date', '')
                    hora_colombia = '--:--'
                    fecha_colombia = ''
                    
                    if fecha_utc:
                        try:
                            fecha_dt = datetime.fromisoformat(fecha_utc.replace('Z', '+00:00'))
                            tz_bogota = pytz.timezone('America/Bogota')
                            fecha_bogota = fecha_dt.astimezone(tz_bogota)
                            hora_colombia = fecha_bogota.strftime('%H:%M')
                            fecha_colombia = fecha_bogota.strftime('%Y-%m-%d')
                        except:
                            pass
                    
                    marcador_local = int(local.get('score', 0)) if local.get('score') else None
                    marcador_visitante = int(visitante.get('score', 0)) if visitante.get('score') else None
                    
                    partido = {
                        'idEvent': f"espn_{evento.get('id', '')}",
                        'strHomeTeam': local.get('name', 'Local'),
                        'strAwayTeam': visitante.get('name', 'Visitante'),
                        'strLeague': 'Liga BetPlay Dimayor',
                        'idLeague': '4497',
                        'dateEvent': fecha_colombia,
                        'strTime': hora_colombia + ':00',
                        'strStatus': 'FT' if estado_tipo == 'post' else ('LIVE' if estado_tipo == 'in' else 'NS'),
                        'strVenue': competencia.get('venue', {}).get('fullName', ''),
                        'strCountry': 'Colombia',
                        'strHomeTeamBadge': local.get('logo', ''),
                        'strAwayTeamBadge': visitante.get('logo', ''),
                        'intHomeScore': marcador_local,
                        'intAwayScore': marcador_visitante,
                        'fuente': 'espn'
                    }
                    partidos.append(partido)
                except:
                    continue
    except Exception as e:
        print(f"❌ Error ESPN Colombia: {e}")
    return partidos

def obtener_partidos_espn_copa():
    """Obtiene partidos de la Copa BetPlay desde ESPN"""
    partidos = []
    try:
        response = requests.get(ESPN_COPA_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            eventos = data.get('events', [])
            for evento in eventos:
                try:
                    competencia = evento.get('competitions', [{}])[0]
                    competidores = competencia.get('competitors', [])
                    local = competidores[0] if len(competidores) > 0 else {}
                    visitante = competidores[1] if len(competidores) > 1 else {}
                    
                    estado_tipo = evento.get('status', {}).get('type', {}).get('state', '')
                    fecha_utc = evento.get('date', '')
                    hora_colombia = '--:--'
                    fecha_colombia = ''
                    
                    if fecha_utc:
                        try:
                            fecha_dt = datetime.fromisoformat(fecha_utc.replace('Z', '+00:00'))
                            tz_bogota = pytz.timezone('America/Bogota')
                            fecha_bogota = fecha_dt.astimezone(tz_bogota)
                            hora_colombia = fecha_bogota.strftime('%H:%M')
                            fecha_colombia = fecha_bogota.strftime('%Y-%m-%d')
                        except:
                            pass
                    
                    partido = {
                        'idEvent': f"espn_copa_{evento.get('id', '')}",
                        'strHomeTeam': local.get('name', 'Local'),
                        'strAwayTeam': visitante.get('name', 'Visitante'),
                        'strLeague': 'Copa BetPlay',
                        'idLeague': '5183',
                        'dateEvent': fecha_colombia,
                        'strTime': hora_colombia + ':00',
                        'strStatus': 'FT' if estado_tipo == 'post' else ('LIVE' if estado_tipo == 'in' else 'NS'),
                        'strVenue': competencia.get('venue', {}).get('fullName', ''),
                        'strCountry': 'Colombia',
                        'strHomeTeamBadge': local.get('logo', ''),
                        'strAwayTeamBadge': visitante.get('logo', ''),
                        'intHomeScore': int(local.get('score', 0)) if local.get('score') else None,
                        'intAwayScore': int(visitante.get('score', 0)) if visitante.get('score') else None,
                        'fuente': 'espn_copa'
                    }
                    partidos.append(partido)
                except:
                    continue
    except Exception as e:
        print(f"❌ Error ESPN Copa: {e}")
    return partidos

def obtener_partidos_del_dia(fecha=None):
    if not fecha:
        fecha = obtener_fecha_hoy_bogota()
    try:
        url = f"{THESPORTSDB_URL}/eventsday.php?d={fecha}&s=Soccer"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            eventos = data.get('events', []) or []
            return {'success': True, 'partidos': eventos, 'total': len(eventos), 'fecha': fecha}
        return {'success': False, 'partidos': [], 'total': 0, 'fecha': fecha}
    except:
        return {'success': False, 'partidos': [], 'total': 0, 'fecha': fecha}

def obtener_partidos_liga_pasados(liga_id):
    try:
        url = f"{THESPORTSDB_URL}/eventspastleague.php?id={liga_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {'success': True, 'partidos': data.get('events', []) or [], 'total': len(data.get('events', []))}
        return {'success': False, 'partidos': [], 'total': 0}
    except:
        return {'success': False, 'partidos': [], 'total': 0}

def obtener_partidos_liga_proximos(liga_id):
    try:
        url = f"{THESPORTSDB_URL}/eventsnextleague.php?id={liga_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {'success': True, 'partidos': data.get('events', []) or [], 'total': len(data.get('events', []))}
        return {'success': False, 'partidos': [], 'total': 0}
    except:
        return {'success': False, 'partidos': [], 'total': 0}

def obtener_detalles_partido(evento_id):
    try:
        if evento_id.startswith('espn'):
            return {'success': False, 'error': 'Detalles no disponibles para ESPN'}
        url = f"{THESPORTSDB_URL}/lookupevent.php?id={evento_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            eventos = data.get('events', []) or []
            if eventos:
                return {'success': True, 'partido': eventos[0]}
        return {'success': False, 'error': 'Partido no encontrado'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def obtener_ultimos_partidos_equipo(equipo_id):
    try:
        if not equipo_id or not str(equipo_id).isdigit():
            return {'success': False, 'partidos': []}
        url = f"{THESPORTSDB_URL}/eventslast.php?id={equipo_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {'success': True, 'partidos': data.get('results', []) or []}
        return {'success': False, 'partidos': []}
    except:
        return {'success': False, 'partidos': []}

def generar_prediccion_nvidia(partido_info, forma_local, forma_visitante, partido_finalizado=False):
    if not GEMINI_API_KEY:
        return {'success': False, 'error': 'Motor Didasko AI no configurado'}
    
    try:
        equipo_local = partido_info.get('strHomeTeam', 'Local')
        equipo_visitante = partido_info.get('strAwayTeam', 'Visitante')
        liga = partido_info.get('strLeague', 'Liga')
        
        forma_local_txt = "\n".join([f"- {p.get('strHomeTeam', '')} {p.get('intHomeScore', '')}-{p.get('intAwayScore', '')} {p.get('strAwayTeam', '')}" for p in (forma_local.get('partidos', []) or [])[:5] if p.get('intHomeScore') is not None])
        forma_visitante_txt = "\n".join([f"- {p.get('strHomeTeam', '')} {p.get('intHomeScore', '')}-{p.get('intAwayScore', '')} {p.get('strAwayTeam', '')}" for p in (forma_visitante.get('partidos', []) or [])[:5] if p.get('intHomeScore') is not None])
        
        prompt = f"""Eres el Profeta Deportivo de Didasko AI.

PARTIDO: {liga} - {equipo_local} vs {equipo_visitante}

FORMA {equipo_local}:
{forma_local_txt or "Sin datos"}

FORMA {equipo_visitante}:
{forma_visitante_txt or "Sin datos"}

Genera predicción en español:

🎯 **GANADOR PROBABLE:** [Equipo o Empate]
📊 **CONFIANZA:** [50-95]%
⚽ **MARCADOR:** [Ej: 2-1]

**ANÁLISIS:**
[3-4 oraciones]

🔥 **DATO:**
[Dato interesante]

️ Predicción IA para entretenimiento."""

        response = requests.post(f"{GEMINI_URL}?key={GEMINI_API_KEY}", json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 500}
        }, timeout=45)
        
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                texto = data['candidates'][0]['content']['parts'][0]['text']
                return {'success': True, 'prediccion': texto, 'ganador': equipo_local, 'confianza': 60, 'ia_usada': 'didasko-ai'}
        return {'success': False, 'error': 'Error en IA'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def obtener_prediccion_cache(partido_id):
    try:
        client = get_client()
        if not client: return None
        result = client.table('predicciones').select('*').eq('partido_id', str(partido_id)).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except:
        return None

def guardar_prediccion_cache(partido_info, prediccion_data):
    try:
        client = get_client()
        if not client: return False
        client.table('predicciones').insert({
            'partido_id': str(partido_info.get('idEvent')),
            'liga': partido_info.get('strLeague', ''),
            'equipo_local': partido_info.get('strHomeTeam', ''),
            'equipo_visitante': partido_info.get('strAwayTeam', ''),
            'fecha_partido': f"{partido_info.get('dateEvent')}T{partido_info.get('strTime', '00:00:00')}",
            'prediccion_texto': prediccion_data.get('prediccion', ''),
            'ganador_predicho': prediccion_data.get('ganador', ''),
            'confianza': prediccion_data.get('confianza', 60),
            'ia_usada': 'didasko-ai',
            'veces_vista': 1
        }).execute()
        return True
    except:
        return False

def verificar_vip(email):
    try:
        client = get_client()
        if not client: return False
        result = client.table('usuarios').select('es_vip, vip_hasta').eq('email', email).execute()
        if result.data and len(result.data) > 0:
            user = result.data[0]
            if user.get('es_vip') and user.get('vip_hasta'):
                vip_hasta = datetime.fromisoformat(user['vip_hasta'].replace('Z', '+00:00'))
                return vip_hasta > datetime.now(vip_hasta.tzinfo)
        return False
    except:
        return False

def contar_vistas_hoy(email):
    try:
        client = get_client()
        if not client: return 0
        hoy = obtener_fecha_hoy_bogota()
        result = client.table('vistas_predicciones').select('id').eq('email', email).eq('fecha_vista', hoy).execute()
        return len(result.data) if result.data else 0
    except:
        return 0

def registrar_vista(email, partido_id):
    try:
        client = get_client()
        if not client: return False
        hoy = obtener_fecha_hoy_bogota()
        client.table('vistas_predicciones').insert({'email': email, 'partido_id': str(partido_id), 'fecha_vista': hoy}).execute()
        return True
    except:
        return False

# ===================================
# ENDPOINTS
# ===================================

@profeta_bp.route('/hoy', methods=['GET'])
def partidos_hoy():
    """Obtiene partidos: ESPN (Colombia) + TheSportsDB (Internacional)"""
    try:
        hoy = obtener_fecha_hoy_bogota()
        
        # 1. ESPN - Colombianos
        espn_liga = obtener_partidos_espn_colombia()
        espn_copa = obtener_partidos_espn_copa()
        colombianos = espn_liga + espn_copa
        
        # 2. TheSportsDB - Internacionales
        tsdb = obtener_partidos_del_dia(hoy)
        internacionales = tsdb.get('partidos', []) if tsdb['success'] else []
        
        # 3. Combinar: Colombianos PRIMERO
        todos = colombianos + internacionales
        
        # 4. Separar programados/finalizados
        programados = [p for p in todos if p.get('strStatus') != 'FT']
        finalizados = [p for p in todos if p.get('strStatus') == 'FT']
        
        # 5. Mostrar programados primero, si no hay, finalizados
        partidos_finales = programados if programados else finalizados
        
        return jsonify({
            'success': True,
            'fecha_hoy': hoy,
            'total_mostrando': len(partidos_finales),
            'partidos': partidos_finales[:20],  # Máximo 20
            'debug': {
                'espn_total': len(colombianos),
                'thesportsdb_total': len(internacionales)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@profeta_bp.route('/liga/<liga_key>/pasados', methods=['GET'])
def partidos_liga_pasados(liga_key):
    if liga_key not in LIGAS_PRIORITARIAS:
        return jsonify({'success': False, 'error': 'Liga no válida'}), 400
    liga = LIGAS_PRIORITARIAS[liga_key]
    resultado = obtener_partidos_liga_pasados(liga['id'])
    if resultado['success']:
        resultado['liga_info'] = liga
    return jsonify(resultado)

@profeta_bp.route('/liga/<liga_key>/proximos', methods=['GET'])
def partidos_liga_proximos(liga_key):
    if liga_key not in LIGAS_PRIORITARIAS:
        return jsonify({'success': False, 'error': 'Liga no válida'}), 400
    liga = LIGAS_PRIORITARIAS[liga_key]
    resultado = obtener_partidos_liga_proximos(liga['id'])
    if resultado['success']:
        resultado['liga_info'] = liga
    return jsonify(resultado)

@profeta_bp.route('/partido/<evento_id>', methods=['GET'])
def detalles_partido(evento_id):
    return jsonify(obtener_detalles_partido(evento_id))

@profeta_bp.route('/ligas', methods=['GET'])
def listar_ligas():
    return jsonify({'success': True, 'total': len(LIGAS_PRIORITARIAS), 'ligas': LIGAS_PRIORITARIAS})

@profeta_bp.route('/predecir/<evento_id>', methods=['GET'])
def predecir_partido(evento_id):
    try:
        email = obtener_email_sesion()
        if not email:
            return jsonify({'success': False, 'error': 'Debes iniciar sesión', 'requiere_login': True}), 401
        
        es_vip = verificar_vip(email)
        cache = obtener_prediccion_cache(evento_id)
        
        if not es_vip:
            vistas_hoy = contar_vistas_hoy(email)
            if vistas_hoy >= 1:
                return jsonify({
                    'success': False, 'error': 'Límite diario alcanzado', 'requiere_vip': True,
                    'mensaje': '🔒 Ya viste tu predicción gratis de hoy. Hazte VIP.',
                    'precio': 'Desde $4.000 COP',
                    'metodo': 'WhatsApp: +57 317 154 7065'
                }), 403
        
        if cache:
            registrar_vista(email, evento_id)
            return jsonify({
                'success': True, 'prediccion': cache['prediccion_texto'], 'ganador': cache['ganador_predicho'],
                'confianza': cache['confianza'], 'ia_usada': 'didasko-ai', 'desde_cache': True, 'es_vip': es_vip
            })
        
        detalles = obtener_detalles_partido(evento_id)
        if not detalles['success']:
            return jsonify({'success': False, 'error': 'Partido no encontrado'}), 404
        
        partido = detalles['partido']
        forma_local = obtener_ultimos_partidos_equipo(partido.get('idHomeTeam'))
        forma_visitante = obtener_ultimos_partidos_equipo(partido.get('idAwayTeam'))
        
        prediccion = generar_prediccion_nvidia(partido, forma_local, forma_visitante)
        
        if prediccion['success']:
            guardar_prediccion_cache(partido, prediccion)
            registrar_vista(email, evento_id)
        
        return jsonify({
            'success': prediccion['success'],
            'prediccion': prediccion.get('prediccion', ''),
            'ganador': prediccion.get('ganador', ''),
            'confianza': prediccion.get('confianza', 60),
            'ia_usada': 'didasko-ai',
            'desde_cache': False,
            'es_vip': es_vip
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@profeta_bp.route('/vip/estado', methods=['GET'])
def estado_vip():
    email = obtener_email_sesion()
    if not email:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    es_vip = verificar_vip(email)
    vistas_hoy = contar_vistas_hoy(email)
    return jsonify({
        'success': True, 'es_vip': es_vip, 'vistas_hoy': vistas_hoy,
        'limite_diario': 999 if es_vip else 1
    })

@profeta_bp.route('/vip/activar', methods=['POST'])
def activar_vip():
    try:
        email = obtener_email_sesion()
        if not email:
            return jsonify({'success': False, 'error': 'No autenticado'}), 401
        
        codigo = request.get_json().get('codigo', '').strip().upper()
        if not codigo:
            return jsonify({'success': False, 'error': 'Código requerido'}), 400
        
        client = get_client()
        result = client.table('codigos_vip').select('*').eq('codigo', codigo).execute()
        if not result.data or not result.data[0].get('activo'):
            return jsonify({'success': False, 'error': 'Código inválido o usado'}), 404
        
        dias = result.data[0].get('dias_duracion', 30)
        vip_hasta = (datetime.now() + timedelta(days=dias)).isoformat()
        
        client.table('usuarios').update({'es_vip': True, 'vip_hasta': vip_hasta}).eq('email', email).execute()
        client.table('codigos_vip').update({'activo': False, 'usado_por': email}).eq('codigo', codigo).execute()
        
        return jsonify({'success': True, 'mensaje': f'VIP activado por {dias} días', 'vip_hasta': vip_hasta})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@profeta_bp.route('/test', methods=['GET'])
def test():
    return jsonify({
        'status': 'ok',
        'version': 'V4.0 - ESPN + TheSportsDB',
        'fecha': obtener_fecha_hoy_bogota()
    })
