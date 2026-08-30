# ===================================
# profeta.py - Profeta Deportivo V4.0 (ESPN + TheSportsDB)
# ===================================
# ESPN API: Partidos colombianos en tiempo real (GRATIS, sin límites)
# TheSportsDB: Ligas internacionales
# IA: Didasko AI (Gemini Flash Lite)
# Cache: Supabase
# ===================================

import os
import time
import requests
import pytz
import re
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session
from supabase_client import get_client

profeta_bp = Blueprint('profeta', __name__)

# ===================================
# CONFIGURACIÓN
# ===================================

THESPORTSDB_KEY = os.getenv('THESPORTSDB_KEY', '123')
THESPORTSDB_URL = f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_KEY}"

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent"

# 🆕 ESPN API - Fútbol Colombiano (GRATIS, sin registro)
ESPN_COLOMBIA_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/col.1/scoreboard"
ESPN_COPA_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/col.cup/scoreboard"

LIGAS_PRIORITARIAS = {
    'champions': {'id': 4480, 'nombre': 'UEFA Champions League', 'pais': 'Europa', 'banner': 'assets/fondos/champions.jpeg'},
    'libertadores': {'id': 4482, 'nombre': 'Copa Libertadores', 'pais': 'Sudamérica', 'banner': 'assets/fondos/libertadores.jpeg'},
    'bundesliga': {'id': 4331, 'nombre': 'Bundesliga', 'pais': 'Alemania', 'banner': 'assets/fondos/bundesliga.jpeg'},
    'laliga': {'id': 4335, 'nombre': 'LaLiga', 'pais': 'España', 'banner': 'assets/fondos/laliga.jpeg'},
    'ligue_1': {'id': 4334, 'nombre': 'Ligue 1', 'pais': 'Francia', 'banner': 'assets/fondos/ligue-1.jpeg'},
    'copa_colombia': {'id': 5183, 'nombre': 'Copa BetPlay', 'pais': 'Colombia', 'banner': 'assets/fondos/copa-colombia.jpeg'},
    'premier': {'id': 4328, 'nombre': 'Premier League', 'pais': 'Inglaterra', 'banner': 'assets/fondos/premier.jpeg'},
    'serie_a': {'id': 4332, 'nombre': 'Serie A', 'pais': 'Italia', 'banner': 'assets/fondos/serie-a.jpeg'},
    'colombia_primera': {'id': 4497, 'nombre': 'Liga BetPlay Dimayor', 'pais': 'Colombia', 'banner': 'assets/fondos/colombia-primera.jpeg'},
    'sudamericana': {'id': 4724, 'nombre': 'Copa Sudamericana', 'pais': 'Sudamérica', 'banner': 'assets/fondos/sudamericana.jpeg'},
}

# ===================================
# HELPERS
# ===================================
def obtener_email_sesion():
    return session.get('usuario_email')

def obtener_fecha_hoy_bogota():
    tz_bogota = pytz.timezone('America/Bogota')
    return datetime.now(tz_bogota).strftime('%Y-%m-%d')

def obtener_fecha_manana_bogota():
    tz_bogota = pytz.timezone('America/Bogota')
    return (datetime.now(tz_bogota) + timedelta(days=1)).strftime('%Y-%m-%d')

# ===================================
# 🆕 ESPN API - PARTIDOS COLOMBIANOS
# ===================================
def obtener_partidos_espn_colombia():
    """Obtiene partidos de la Liga BetPlay desde ESPN (GRATIS, sin límites)"""
    partidos = []
    try:
        print(f"📡 Consultando ESPN Colombia: {ESPN_COLOMBIA_URL}")
        response = requests.get(ESPN_COLOMBIA_URL, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            eventos = data.get('events', [])
            print(f"✅ ESPN devolvió {len(eventos)} partidos colombianos")
            
            for evento in eventos:
                try:
                    competencia = evento.get('competitions', [{}])[0]
                    competidor1 = competencia.get('competitors', [{}])[0]
                    competidor2 = competencia.get('competitors', [{}])[1]
                    
                    # Determinar local y visitante
                    local = competidor1 if competidor1.get('homeAway') == 'home' else competidor2
                    visitante = competidor2 if competidor1.get('homeAway') == 'home' else competidor1
                    
                    estado = evento.get('status', {})
                    estado_tipo = estado.get('type', {}).get('state', '')  # 'pre', 'in', 'post'
                    estado_detalle = estado.get('type', {}).get('shortDetail', '')
                    
                    # Obtener marcadores
                    marcador_local = None
                    marcador_visitante = None
                    if 'score' in local:
                        marcador_local = int(local['score']) if local['score'] else None
                    if 'score' in visitante:
                        marcador_visitante = int(visitante['score']) if visitante['score'] else None
                    
                    # Fecha y hora
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
                    
                    # Escudos
                    escudo_local = local.get('logo', '')
                    escudo_visitante = visitante.get('logo', '')
                    
                    partido = {
                        'idEvent': str(evento.get('id', '')),
                        'strHomeTeam': local.get('name', 'Local'),
                        'strAwayTeam': visitante.get('name', 'Visitante'),
                        'strLeague': 'Liga BetPlay Dimayor',
                        'idLeague': '4497',
                        'dateEvent': fecha_colombia,
                        'strTime': hora_colombia + ':00',
                        'strStatus': 'FT' if estado_tipo == 'post' else ('LIVE' if estado_tipo == 'in' else 'NS'),
                        'strVenue': competencia.get('venue', {}).get('fullName', ''),
                        'strCountry': 'Colombia',
                        'strHomeTeamBadge': escudo_local,
                        'strAwayTeamBadge': escudo_visitante,
                        'intHomeScore': marcador_local,
                        'intAwayScore': marcador_visitante,
                        'fuente': 'espn'
                    }
                    partidos.append(partido)
                    
                except Exception as e:
                    print(f"⚠️ Error procesando evento ESPN: {e}")
                    continue
        else:
            print(f"⚠️ ESPN status {response.status_code}")
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
                    competidor1 = competencia.get('competitors', [{}])[0]
                    competidor2 = competencia.get('competitors', [{}])[1]
                    
                    local = competidor1 if competidor1.get('homeAway') == 'home' else competidor2
                    visitante = competidor2 if competidor1.get('homeAway') == 'home' else competidor1
                    
                    estado = evento.get('status', {})
                    estado_tipo = estado.get('type', {}).get('state', '')
                    
                    marcador_local = int(local.get('score', 0)) if local.get('score') else None
                    marcador_visitante = int(visitante.get('score', 0)) if visitante.get('score') else None
                    
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
                        'idEvent': f"copa_{evento.get('id', '')}",
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
                        'intHomeScore': marcador_local,
                        'intAwayScore': marcador_visitante,
                        'fuente': 'espn_copa'
                    }
                    partidos.append(partido)
                except:
                    continue
    except Exception as e:
        print(f"❌ Error ESPN Copa: {e}")
    
    return partidos


# ===================================
# TheSportsDB - Ligas Internacionales
# ===================================
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
        
        return {'success': False, 'error': f'Código {response.status_code}', 'partidos': [], 'total': 0, 'fecha': fecha}
    except Exception as e:
        return {'success': False, 'error': str(e), 'partidos': [], 'total': 0, 'fecha': fecha}


def obtener_partidos_liga_pasados(liga_id):
    try:
        url = f"{THESPORTSDB_URL}/eventspastleague.php?id={liga_id}"
        response = requests.get(url, timeout=10)
        partidos = []
        if response.status_code == 200:
            data = response.json()
            partidos = data.get('events', []) or []
        return {'success': True, 'partidos': partidos, 'total': len(partidos)}
    except Exception as e:
        return {'success': False, 'error': str(e), 'partidos': [], 'total': 0}


def obtener_partidos_liga_proximos(liga_id):
    try:
        url = f"{THESPORTSDB_URL}/eventsnextleague.php?id={liga_id}"
        response = requests.get(url, timeout=10)
        partidos = []
        if response.status_code == 200:
            data = response.json()
            partidos = data.get('events', []) or []
        return {'success': True, 'partidos': partidos, 'total': len(partidos)}
    except Exception as e:
        return {'success': False, 'error': str(e), 'partidos': [], 'total': 0}


def obtener_detalles_partido(evento_id):
    try:
        # Si es de ESPN, buscar en caché primero
        if evento_id.startswith('copa_') or '_' in evento_id:
            client = get_client()
            if client:
                result = client.table('partidos').select('*').eq('partido_id_externo', str(evento_id)).execute()
                if result.data and len(result.data) > 0:
                    p = result.data[0]
                    return {
                        'success': True,
                        'partido': {
                            'idEvent': p['partido_id_externo'],
                            'strHomeTeam': p['equipo_local'],
                            'strAwayTeam': p['equipo_visitante'],
                            'strLeague': p['liga'],
                            'dateEvent': p['fecha_partido'].split('T')[0] if p.get('fecha_partido') else '',
                            'strTime': p['fecha_partido'].split('T')[1] if p.get('fecha_partido') and 'T' in p['fecha_partido'] else '00:00:00',
                            'strVenue': p.get('estadio', ''),
                            'strCountry': 'Colombia',
                            'strStatus': 'FT' if p.get('estado') == 'jugado' else 'NS',
                            'intHomeScore': p.get('resultado_local'),
                            'intAwayScore': p.get('resultado_visitante'),
                            'strHomeTeamBadge': 'assets/logo/buho-mascota.png',
                            'strAwayTeamBadge': 'assets/logo/buho-mascota.png',
                        }
                    }
        
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
        url = f"{THESPORTSDB_URL}/eventslast.php?id={equipo_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            eventos = data.get('results', []) or []
            return {'success': True, 'partidos': eventos}
        return {'success': False, 'error': f'Código {response.status_code}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ===================================
# 🔮 PREDICCIÓN CON IA
# ===================================
def generar_prediccion_nvidia(partido_info, forma_local, forma_visitante, partido_finalizado=False):
    if not GEMINI_API_KEY:
        return {'success': False, 'error': 'Motor Didasko AI no configurado'}
    
    try:
        equipo_local = partido_info.get('strHomeTeam', 'Local')
        equipo_visitante = partido_info.get('strAwayTeam', 'Visitante')
        liga = partido_info.get('strLeague', 'Liga')
        fecha = partido_info.get('dateEvent', '')
        estadio = partido_info.get('strVenue', '')
        
        resultado_real = ""
        if partido_finalizado and partido_info.get('intHomeScore') is not None:
            resultado_real = f"\n⚠️ NOTA: Este partido YA SE JUGÓ. El resultado final fue {equipo_local} {partido_info.get('intHomeScore')} - {partido_info.get('intAwayScore')} {equipo_visitante}. Pero analiza SOLO como si no supieras el resultado."
        
        forma_local_txt = ""
        if forma_local.get('success') and forma_local.get('partidos'):
            for p in forma_local['partidos'][:5]:
                if p.get('intHomeScore') is not None:
                    forma_local_txt += f"- {p.get('strHomeTeam')} {p.get('intHomeScore')}-{p.get('intAwayScore')} {p.get('strAwayTeam')}\n"
        
        forma_visitante_txt = ""
        if forma_visitante.get('success') and forma_visitante.get('partidos'):
            for p in forma_visitante['partidos'][:5]:
                if p.get('intHomeScore') is not None:
                    forma_visitante_txt += f"- {p.get('strHomeTeam')} {p.get('intHomeScore')}-{p.get('intAwayScore')} {p.get('strAwayTeam')}\n"
        
        prompt = f"""Eres el Profeta Deportivo de Didasko AI, un experto analista de fútbol.{resultado_real}

PARTIDO A ANALIZAR:
🏆 Liga: {liga}
📅 {equipo_local} vs {equipo_visitante}
📅 Fecha: {fecha}
🏟️ Estadio: {estadio}

FORMA RECIENTE DE {equipo_local}:
{forma_local_txt if forma_local_txt else "Sin datos recientes disponibles"}

FORMA RECIENTE DE {equipo_visitante}:
{forma_visitante_txt if forma_visitante_txt else "Sin datos recientes disponibles"}

Genera una predicción PROFESIONAL y ENTRETENIDA en español con esta estructura EXACTA:

🎯 **GANADOR PROBABLE:** [Nombre del equipo o "Empate"]
📊 **CONFIANZA:** [Número del 50 al 95]%
⚽ **MARCADOR PREDICHO:** [Ej: 2-1]

 **ANÁLISIS:**
[3-4 oraciones cortas analizando la forma de ambos equipos, ventajas y factores clave]

🔥 **DATO CURIOSO:**
[Un dato interesante o predicción específica]

⚠️ Nota: Esta es una predicción con IA para entretenimiento. No es garantía de resultado."""

        url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 500, "topP": 0.9}
        }
        
        print("🔮 Didasko AI generando predicción...")
        response = requests.post(url, json=payload, timeout=45)
        
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                candidate = data['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    texto = candidate['content']['parts'][0]['text']
                    print("✅ Didasko AI respondió correctamente")
                    
                    ganador = equipo_local
                    confianza = 60
                    
                    try:
                        if 'GANADOR PROBABLE' in texto:
                            linea_ganador = [l for l in texto.split('\n') if 'GANADOR PROBABLE' in l][0]
                            if equipo_visitante.lower() in linea_ganador.lower():
                                ganador = equipo_visitante
                            elif 'empate' in linea_ganador.lower():
                                ganador = 'Empate'
                        
                        if 'CONFIANZA' in texto:
                            linea_conf = [l for l in texto.split('\n') if 'CONFIANZA' in l][0]
                            nums = re.findall(r'\d+', linea_conf)
                            if nums:
                                confianza = int(nums[0])
                    except:
                        pass
                    
                    return {'success': True, 'prediccion': texto, 'ganador': ganador, 'confianza': confianza, 'ia_usada': 'didasko-ai'}
            
            return {'success': False, 'error': 'Respuesta sin contenido válido'}
        else:
            print(f"⚠️ Motor Didasko AI código {response.status_code}: {response.text[:200]}")
            return {'success': False, 'error': f'Motor Didasko AI error: {response.status_code}'}
    
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Motor Didasko AI tardó demasiado. Intenta de nuevo.'}
    except Exception as e:
        return {'success': False, 'error': f'Error generando predicción: {str(e)}'}


# ===================================
# 💾 CACHE EN SUPABASE
# ===================================
def obtener_prediccion_cache(partido_id):
    try:
        client = get_client()
        if not client: return None
        result = client.table('predicciones').select('*').eq('partido_id', str(partido_id)).execute()
        if result.data and len(result.data) > 0:
            pred = result.data[0]
            client.table('predicciones').update({'veces_vista': (pred.get('veces_vista', 0) or 0) + 1}).eq('id', pred['id']).execute()
            return pred
        return None
    except Exception as e:
        return None


def guardar_prediccion_cache(partido_info, prediccion_data):
    try:
        client = get_client()
        if not client: return False
        prediccion = {
            'partido_id': str(partido_info.get('idEvent')),
            'liga': partido_info.get('strLeague', ''),
            'equipo_local': partido_info.get('strHomeTeam', ''),
            'equipo_visitante': partido_info.get('strAwayTeam', ''),
            'fecha_partido': f"{partido_info.get('dateEvent')}T{partido_info.get('strTime', '00:00:00')}",
            'prediccion_texto': prediccion_data.get('prediccion', ''),
            'ganador_predicho': prediccion_data.get('ganador', ''),
            'confianza': prediccion_data.get('confianza', 60),
            'ia_usada': prediccion_data.get('ia_usada', 'didasko-ai'),
            'veces_vista': 1
        }
        client.table('predicciones').insert(prediccion).execute()
        return True
    except Exception as e:
        print(f"⚠️ Error guardando predicción: {e}")
        return False


def guardar_partido_cache(partido_data):
    try:
        client = get_client()
        if not client: return
        partido = {
            'partido_id_externo': str(partido_data.get('idEvent')),
            'liga': partido_data.get('strLeague', ''),
            'equipo_local': partido_data.get('strHomeTeam', ''),
            'equipo_visitante': partido_data.get('strAwayTeam', ''),
            'fecha_partido': f"{partido_data.get('dateEvent')}T{partido_data.get('strTime', '00:00:00')}",
            'estadio': partido_data.get('strVenue', ''),
            'ciudad': partido_data.get('strCity', ''),
            'estado': 'jugado' if partido_data.get('strStatus') == 'FT' else 'programado'
        }
        if partido_data.get('intHomeScore') is not None:
            partido['resultado_local'] = int(partido_data.get('intHomeScore', 0))
        if partido_data.get('intAwayScore') is not None:
            partido['resultado_visitante'] = int(partido_data.get('intAwayScore', 0))
        
        existente = client.table('partidos').select('id').eq('partido_id_externo', partido['partido_id_externo']).execute()
        if existente.data:
            client.table('partidos').update(partido).eq('partido_id_externo', partido['partido_id_externo']).execute()
        else:
            client.table('partidos').insert(partido).execute()
        return True
    except Exception as e:
        print(f"️ Error guardando partido: {e}")
        return False


# ===================================
# 👤 SISTEMA VIP
# ===================================
def verificar_vip(email):
    try:
        client = get_client()
        if not client: return False
        result = client.table('usuarios').select('es_vip, vip_hasta').eq('email', email).execute()
        if result.data and len(result.data) > 0:
            user = result.data[0]
            if user.get('es_vip'):
                if user.get('vip_hasta'):
                    vip_hasta = datetime.fromisoformat(user['vip_hasta'].replace('Z', '+00:00'))
                    if vip_hasta > datetime.now(vip_hasta.tzinfo):
                        return True
                    else:
                        client.table('usuarios').update({'es_vip': False}).eq('email', email).execute()
                        return False
        return False
    except Exception as e:
        return False


def contar_vistas_hoy(email):
    try:
        client = get_client()
        if not client: return 0
        hoy = obtener_fecha_hoy_bogota()
        result = client.table('vistas_predicciones').select('id').eq('email', email).eq('fecha_vista', hoy).execute()
        return len(result.data) if result.data else 0
    except Exception as e:
        return 0


def registrar_vista(email, partido_id):
    try:
        client = get_client()
        if not client: return False
        hoy = obtener_fecha_hoy_bogota()
        existente = client.table('vistas_predicciones').select('id').eq('email', email).eq('partido_id', str(partido_id)).eq('fecha_vista', hoy).execute()
        if existente.data and len(existente.data) > 0:
            return True
        client.table('vistas_predicciones').insert({'email': email, 'partido_id': str(partido_id), 'fecha_vista': hoy}).execute()
        return True
    except Exception as e:
        return False


# ===================================
# 🎯 ENDPOINT /hoy - ESPN + TheSportsDB
# ===================================
@profeta_bp.route('/hoy', methods=['GET'])
def partidos_hoy():
    """Obtiene partidos de ESPN (Colombia) + TheSportsDB (Internacional)"""
    try:
        hoy_bogota = obtener_fecha_hoy_bogota()
        manana_bogota = obtener_fecha_manana_bogota()
        
        print(f"\n{'='*60}")
        print(f"📅 FECHA HOY Colombia: {hoy_bogota}")
        print(f"📅 FECHA MAÑANA Colombia: {manana_bogota}")
        print(f"{'='*60}")
        
        # 🆕 1. Obtener partidos colombianos de ESPN
        print("\n🇴 CONSULTANDO ESPN COLOMBIA...")
        partidos_espn_liga = obtener_partidos_espn_colombia()
        partidos_espn_copa = obtener_partidos_espn_copa()
        partidos_colombianos = partidos_espn_liga + partidos_espn_copa
        print(f"✅ Total partidos colombianos de ESPN: {len(partidos_colombianos)}")
        
        # 2. Obtener partidos internacionales de TheSportsDB (hoy y mañana)
        print("\n🌍 CONSULTANDO TheSportsDB...")
        resultado_hoy = obtener_partidos_del_dia(hoy_bogota)
        resultado_manana = obtener_partidos_del_dia(manana_bogota)
        
        partidos_internacionales = []
        if resultado_hoy['success']:
            partidos_internacionales.extend(resultado_hoy['partidos'])
        if resultado_manana['success']:
            partidos_internacionales.extend(resultado_manana['partidos'])
        
        # Filtrar solo ligas prioritarias (no colombianas, ya las tenemos de ESPN)
        ids_colombianas = ['4497', '5183']
        ids_prioritarias = [str(liga['id']) for liga in LIGAS_PRIORITARIAS.values()]
        partidos_internacionales = [
            p for p in partidos_internacionales 
            if str(p.get('idLeague')) in ids_prioritarias 
            and str(p.get('idLeague')) not in ids_colombianas
        ]
        print(f"✅ Partidos internacionales prioritarios: {len(partidos_internacionales)}")
        
        # 3. COMBINAR: Colombianos PRIMERO + Internacionales
        todos_programados = []
        todos_finalizados = []
        
        # Colombianos
        for p in partidos_colombianos:
            if p.get('strStatus') == 'FT':
                todos_finalizados.append(p)
            else:
                todos_programados.append(p)
        
        # Internacionales
        for p in partidos_internacionales:
            if p.get('strStatus') == 'FT':
                todos_finalizados.append(p)
            else:
                todos_programados.append(p)
        
        print(f"\n📊 TOTAL programados: {len(todos_programados)}")
        print(f"📊 TOTAL finalizados: {len(todos_finalizados)}")
        
        # Guardar en caché
        for p in todos_programados + todos_finalizados:
            guardar_partido_cache(p)
        
        # 4. PRIORIZAR: Colombianos primero, luego internacionales
        partidos_finales = []
        
        # Colombianos programados
        colombianos_prog = [p for p in todos_programados if str(p.get('idLeague')) in ids_colombianas or p.get('fuente', '').startswith('espn')]
        partidos_finales.extend(colombianos_prog)
        
        # Internacionales programados (hasta completar 15)
        if len(partidos_finales) < 15:
            internacionales_prog = [p for p in todos_programados if p not in colombianos_prog]
            partidos_finales.extend(internacionales_prog[:15-len(partidos_finales)])
        
        # Si no hay programados, mostrar finalizados
        if not partidos_finales and todos_finalizados:
            colombianos_fin = [p for p in todos_finalizados if str(p.get('idLeague')) in ids_colombianas or p.get('fuente', '').startswith('espn')]
            partidos_finales.extend(colombianos_fin)
            if len(partidos_finales) < 15:
                internacionales_fin = [p for p in todos_finalizados if p not in colombianos_fin]
                partidos_finales.extend(internacionales_fin[:15-len(partidos_finales)])
        
        print(f"\n🎯 MOSTRANDO {len(partidos_finales)} partidos")
        if colombianos_prog:
            print(f"🇨🇴 Colombianos: {len(colombianos_prog)}")
            for p in colombianos_prog[:5]:
                print(f"   ⚽ {p.get('strHomeTeam')} vs {p.get('strAwayTeam')} - {p.get('dateEvent')} {p.get('strTime')}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': True,
            'fecha_hoy': hoy_bogota,
            'fecha_manana': manana_bogota,
            'total_colombianos': len(partidos_colombianos),
            'total_internacionales': len(partidos_internacionales),
            'total_mostrando': len(partidos_finales),
            'partidos': partidos_finales,
            'debug': {
                'espn_liga': len(partidos_espn_liga),
                'espn_copa': len(partidos_espn_copa),
                'thesportsdb_hoy': resultado_hoy['total'],
                'thesportsdb_manana': resultado_manana['total']
            }
        })
    except Exception as e:
        print(f"❌ Error en /hoy: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ===================================
# OTROS ENDPOINTS
# ===================================
@profeta_bp.route('/liga/<liga_key>/pasados', methods=['GET'])
def partidos_liga_pasados(liga_key):
    try:
        if liga_key not in LIGAS_PRIORITARIAS:
            return jsonify({'success': False, 'error': 'Liga no válida'}), 400
        liga = LIGAS_PRIORITARIAS[liga_key]
        resultado = obtener_partidos_liga_pasados(liga['id'])
        if resultado['success']:
            resultado['liga_info'] = liga
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@profeta_bp.route('/liga/<liga_key>/proximos', methods=['GET'])
def partidos_liga_proximos(liga_key):
    try:
        if liga_key not in LIGAS_PRIORITARIAS:
            return jsonify({'success': False, 'error': 'Liga no válida'}), 400
        liga = LIGAS_PRIORITARIAS[liga_key]
        resultado = obtener_partidos_liga_proximos(liga['id'])
        if resultado['success']:
            resultado['liga_info'] = liga
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@profeta_bp.route('/partido/<evento_id>', methods=['GET'])
def detalles_partido(evento_id):
    try:
        resultado = obtener_detalles_partido(evento_id)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@profeta_bp.route('/ligas', methods=['GET'])
def listar_ligas():
    return jsonify({'success': True, 'total': len(LIGAS_PRIORITARIAS), 'ligas': LIGAS_PRIORITARIAS})


# ===================================
# 🔮 ENDPOINT PREDECIR
# ===================================
@profeta_bp.route('/predecir/<evento_id>', methods=['GET'])
def predecir_partido(evento_id):
    try:
        email = obtener_email_sesion()
        if not email:
            return jsonify({'success': False, 'error': 'Debes iniciar sesión', 'requiere_login': True}), 401
        
        es_vip = verificar_vip(email)
        cache = obtener_prediccion_cache(evento_id)
        ya_vio_este = False
        
        if cache:
            client = get_client()
            hoy = obtener_fecha_hoy_bogota()
            visto = client.table('vistas_predicciones').select('id').eq('email', email).eq('partido_id', str(evento_id)).eq('fecha_vista', hoy).execute()
            ya_vio_este = bool(visto.data)
        
        if not es_vip and not ya_vio_este:
            vistas_hoy = contar_vistas_hoy(email)
            if vistas_hoy >= 1:
                return jsonify({
                    'success': False, 'error': 'Límite diario alcanzado', 'requiere_vip': True,
                    'mensaje': '🔒 Ya viste tu predicción gratis de hoy. Hazte VIP para ver todas.',
                    'precio': 'Aporte desde $4.000 COP en adelante',
                    'metodo': 'Contáctame por WhatsApp y te ayudo con tu código VIP'
                }), 403
        
        if cache:
            registrar_vista(email, evento_id)
            return jsonify({
                'success': True, 'prediccion': cache['prediccion_texto'], 'ganador': cache['ganador_predicho'],
                'confianza': cache['confianza'], 'ia_usada': 'didasko-ai', 'fecha_generada': cache.get('fecha_generada'),
                'desde_cache': True, 'es_vip': es_vip, 'partido_finalizado': False
            })
        
        detalles = obtener_detalles_partido(evento_id)
        if not detalles['success']:
            return jsonify({'success': False, 'error': 'No se pudo obtener información del partido'}), 404
        
        partido = detalles['partido']
        partido_finalizado = partido.get('strStatus') == 'FT'
        
        id_local = partido.get('idHomeTeam')
        id_visitante = partido.get('idAwayTeam')
        
        forma_local = obtener_ultimos_partidos_equipo(id_local) if id_local else {'success': False, 'partidos': []}
        forma_visitante = obtener_ultimos_partidos_equipo(id_visitante) if id_visitante else {'success': False, 'partidos': []}
        
        prediccion = generar_prediccion_nvidia(partido, forma_local, forma_visitante, partido_finalizado=partido_finalizado)
        
        if not prediccion['success']:
            return jsonify(prediccion), 500
        
        guardar_prediccion_cache(partido, prediccion)
        registrar_vista(email, evento_id)
        
        resultado_real = None
        if partido_finalizado and partido.get('intHomeScore') is not None:
            resultado_real = {
                'local': partido.get('strHomeTeam'),
                'visitante': partido.get('strAwayTeam'),
                'goles_local': partido.get('intHomeScore'),
                'goles_visitante': partido.get('intAwayScore')
            }
        
        return jsonify({
            'success': True, 
            'prediccion': prediccion['prediccion'], 
            'ganador': prediccion['ganador'],
            'confianza': prediccion['confianza'], 
            'ia_usada': 'didasko-ai', 
            'desde_cache': False, 
            'es_vip': es_vip,
            'partido_finalizado': partido_finalizado,
            'prediccion_retroactiva': partido_finalizado,
            'resultado_real': resultado_real
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error interno: {str(e)}'}), 500


# ===================================
# 💎 VIP
# ===================================
@profeta_bp.route('/vip/estado', methods=['GET'])
def estado_vip():
    try:
        email = obtener_email_sesion()
        if not email: return jsonify({'success': False, 'error': 'No autenticado'}), 401
        es_vip = verificar_vip(email)
        vistas_hoy = contar_vistas_hoy(email)
        vip_hasta = None
        if es_vip:
            client = get_client()
            result = client.table('usuarios').select('vip_hasta').eq('email', email).execute()
            if result.data: vip_hasta = result.data[0].get('vip_hasta')
        
        return jsonify({
            'success': True, 'es_vip': es_vip, 'vip_hasta': vip_hasta, 'vistas_hoy': vistas_hoy,
            'limite_diario': 999 if es_vip else 1, 'vistas_restantes': 999 if es_vip else max(0, 1 - vistas_hoy)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@profeta_bp.route('/vip/activar', methods=['POST'])
def activar_vip():
    try:
        email = obtener_email_sesion()
        if not email: return jsonify({'success': False, 'error': 'No autenticado'}), 401
        data = request.get_json()
        codigo = data.get('codigo', '').strip().upper()
        if not codigo: return jsonify({'success': False, 'error': 'Código requerido'}), 400
        
        client = get_client()
        result = client.table('codigos_vip').select('*').eq('codigo', codigo).execute()
        if not result.data: return jsonify({'success': False, 'error': 'Código inválido'}), 404
        codigo_data = result.data[0]
        if not codigo_data.get('activo') or codigo_data.get('usado_por'):
            return jsonify({'success': False, 'error': 'Código ya usado o inactivo'}), 400
        
        dias = codigo_data.get('dias_duracion', 30)
        vip_hasta = (datetime.now() + timedelta(days=dias)).isoformat()
        
        client.table('usuarios').update({'es_vip': True, 'vip_hasta': vip_hasta, 'codigo_vip_usado': codigo}).eq('email', email).execute()
        client.table('codigos_vip').update({'activo': False, 'usado_por': email, 'email_usuario': email, 'fecha_uso': datetime.now().isoformat()}).eq('codigo', codigo).execute()
        
        return jsonify({'success': True, 'mensaje': f'¡VIP activado por {dias} días! 🎉', 'vip_hasta': vip_hasta, 'dias_activos': dias})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===================================
# 🧪 TEST Y DEBUG
# ===================================
@profeta_bp.route('/test', methods=['GET'])
def test():
    try:
        response = requests.get(f"{THESPORTSDB_URL}/lookupteam.php?id=137617", timeout=5)
        api_ok = response.status_code == 200
        
        response_espn = requests.get(ESPN_COLOMBIA_URL, timeout=5)
        espn_ok = response_espn.status_code == 200
    except:
        api_ok = False
        espn_ok = False
    
    return jsonify({
        'status': 'ok', 
        'version': 'V4.0 - ESPN + TheSportsDB',
        'thesportsdb_ok': api_ok, 
        'espn_colombia_ok': espn_ok,
        'didasko_ai_configurada': bool(GEMINI_API_KEY),
        'ligas_configuradas': len(LIGAS_PRIORITARIAS),
        'sesion_activa': bool(session.get('usuario_email')),
        'fecha_servidor_bogota': obtener_fecha_hoy_bogota()
    })


@profeta_bp.route('/debug', methods=['GET'])
def debug():
    hoy = obtener_fecha_hoy_bogota()
    
    # ESPN
    espn_liga = obtener_partidos_espn_colombia()
    espn_copa = obtener_partidos_espn_copa()
    
    # TheSportsDB
    tsdb = obtener_partidos_del_dia(hoy)
    
    return jsonify({
        'fecha_hoy': hoy,
        'espn_liga_total': len(espn_liga),
        'espn_copa_total': len(espn_copa),
        'thesportsdb_total': tsdb['total'],
        'espn_liga_ejemplos': espn_liga[:3],
        'espn_copa_ejemplos': espn_copa[:3],
        'thesportsdb_ejemplos': tsdb['partidos'][:3] if tsdb['partidos'] else []
    })
