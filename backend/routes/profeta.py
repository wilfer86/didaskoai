# ===================================
# profeta.py - Profeta Deportivo V3.7 (Corregido Zona Horaria + Fallback)
# ===================================
# Agente autónomo de predicciones deportivas
# API: TheSportsDB (gratis)
# IA: Didasko AI (motor Gemini Flash Lite Latest)
# Cache: Supabase para eficiencia con Fallback inteligente
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

# 🤖 Motor Didasko AI (interno - Gemini Flash Lite súper rápido)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent"

# 🌍 Ligas prioritarias con banners
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
# 🔐 HELPER: Obtener email de sesión
# ===================================
def obtener_email_sesion():
    return session.get('usuario_email')

# ===================================
# 🕒 CORRECCIÓN CRÍTICA: Zona Horaria Colombia
# ===================================
def obtener_fecha_hoy_bogota():
    """Devuelve la fecha de HOY en Colombia (YYYY-MM-DD), sin importar dónde esté el servidor."""
    tz_bogota = pytz.timezone('America/Bogota')
    return datetime.now(tz_bogota).strftime('%Y-%m-%d')

# ===================================
# FUNCIONES DE THESPORTSDB (OPTIMIZADAS)
# ===================================

def obtener_partidos_del_dia(fecha=None):
    """Obtiene todos los partidos de fútbol de una fecha específica."""
    if not fecha:
        fecha = obtener_fecha_hoy_bogota() # <-- Usa hora Colombia por defecto
    
    try:
        url = f"{THESPORTSDB_URL}/eventsday.php?d={fecha}&s=Soccer"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            eventos = data.get('events', []) or []
            return {'success': True, 'partidos': eventos, 'total': len(eventos)}
        
        if response.status_code == 429:
            return {'success': False, 'error': 'Límite de API alcanzado. Usando caché.', 'partidos': [], 'total': 0}
        
        return {'success': False, 'error': f'Código {response.status_code}', 'partidos': [], 'total': 0}
    except Exception as e:
        return {'success': False, 'error': str(e), 'partidos': [], 'total': 0}


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
# 🔮 GENERAR PREDICCIÓN CON DIDASKO AI
# ===================================
def generar_prediccion_nvidia(partido_info, forma_local, forma_visitante):
    if not GEMINI_API_KEY:
        return {'success': False, 'error': 'Motor Didasko AI no configurado'}
    
    try:
        equipo_local = partido_info.get('strHomeTeam', 'Local')
        equipo_visitante = partido_info.get('strAwayTeam', 'Visitante')
        liga = partido_info.get('strLeague', 'Liga')
        fecha = partido_info.get('dateEvent', '')
        estadio = partido_info.get('strVenue', '')
        
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
        
        prompt = f"""Eres el Profeta Deportivo de Didasko AI, un experto analista de fútbol.

PARTIDO A ANALIZAR:
🏆 Liga: {liga}
⚽ {equipo_local} vs {equipo_visitante}
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

📝 **ANÁLISIS:**
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
# 💾 CACHE DE PREDICCIONES Y PARTIDOS EN SUPABASE
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
        print(f"⚠️ Error buscando cache: {e}")
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
        print(f"⚠️ Error guardando partido: {e}")
        return False


# ===================================
# 👤 SISTEMA VIP - VERIFICACIONES
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
        print(f"⚠️ Error verificando VIP: {e}")
        return False


def contar_vistas_hoy(email):
    try:
        client = get_client()
        if not client: return 0
        hoy = obtener_fecha_hoy_bogota()
        result = client.table('vistas_predicciones').select('id').eq('email', email).eq('fecha_vista', hoy).execute()
        return len(result.data) if result.data else 0
    except Exception as e:
        print(f"⚠️ Error contando vistas: {e}")
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
        print(f"⚠️ Error registrando vista: {e}")
        return False


# ===================================
# 🎯 ENDPOINTS PÚBLICOS
# ===================================

@profeta_bp.route('/hoy', methods=['GET'])
def partidos_hoy():
    """Devuelve los partidos importantes del día con Fallback inteligente."""
    try:
        hoy_bogota = obtener_fecha_hoy_bogota()
        resultado_api = obtener_partidos_del_dia(hoy_bogota)
        partidos_finales = []
        fuente_datos = 'api'
        
        ids_prioritarios = [str(liga['id']) for liga in LIGAS_PRIORITARIAS.values()]
        nombres_prioritarios = [liga['nombre'] for liga in LIGAS_PRIORITARIAS.values()]
        
        # 1. Intentar usar datos frescos de la API
        if resultado_api['success'] and resultado_api['total'] > 0:
            partidos_finales = [
                p for p in resultado_api['partidos']
                if str(p.get('idLeague', '')) in ids_prioritarios
            ]
            # Actualizar caché con lo más reciente
            for partido in partidos_finales:
                guardar_partido_cache(partido)
        else:
            # 2. FALLBACK: Si la API falla o no hay datos, usar Supabase
            print(f"⚠️ API falló o sin partidos para {hoy_bogota}. Usando caché de Supabase.")
            fuente_datos = 'cache'
            client = get_client()
            if client:
                # Buscar partidos en Supabase que coincidan con la fecha de hoy en Colombia
                res = client.table('partidos').select('*').ilike('fecha_partido', f"{hoy_bogota}%").execute()
                if res.data:
                    partidos_finales = [
                        p for p in res.data
                        if p.get('liga') in nombres_prioritarios
                    ]
        
        return jsonify({
            'success': True,
            'fecha': hoy_bogota,
            'total_prioritarios': len(partidos_finales),
            'partidos': partidos_finales,
            'fuente': fuente_datos # Para que el frontend sepa si es fresco o caché
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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
# 🔮 ENDPOINT PREDECIR CON IA
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
                'desde_cache': True, 'es_vip': es_vip
            })
        
        detalles = obtener_detalles_partido(evento_id)
        if not detalles['success']:
            return jsonify({'success': False, 'error': 'No se pudo obtener información del partido'}), 404
        
        partido = detalles['partido']
        id_local = partido.get('idHomeTeam')
        id_visitante = partido.get('idAwayTeam')
        
        forma_local = obtener_ultimos_partidos_equipo(id_local) if id_local else {'success': False, 'partidos': []}
        forma_visitante = obtener_ultimos_partidos_equipo(id_visitante) if id_visitante else {'success': False, 'partidos': []}
        
        prediccion = generar_prediccion_nvidia(partido, forma_local, forma_visitante)
        if not prediccion['success']:
            return jsonify(prediccion), 500
        
        guardar_prediccion_cache(partido, prediccion)
        registrar_vista(email, evento_id)
        
        return jsonify({
            'success': True, 'prediccion': prediccion['prediccion'], 'ganador': prediccion['ganador'],
            'confianza': prediccion['confianza'], 'ia_usada': 'didasko-ai', 'desde_cache': False, 'es_vip': es_vip
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error interno: {str(e)}'}), 500


# ===================================
# 💎 ENDPOINTS SISTEMA VIP
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
# 🧪 TEST
# ===================================
@profeta_bp.route('/test', methods=['GET'])
def test():
    try:
        response = requests.get(f"{THESPORTSDB_URL}/lookupteam.php?id=137617", timeout=5)
        api_ok = response.status_code == 200
    except:
        api_ok = False
    
    return jsonify({
        'status': 'ok', 'endpoint': 'profeta', 'version': 'V3.7 - Zona Horaria Corregida + Fallback',
        'thesportsdb_key': THESPORTSDB_KEY, 'didasko_ai_configurada': bool(GEMINI_API_KEY),
        'api_conectada': api_ok, 'ligas_configuradas': len(LIGAS_PRIORITARIAS),
        'sesion_activa': bool(session.get('usuario_email')), 'usuario_actual': session.get('usuario_email', 'no logueado'),
        'fecha_servidor_bogota': obtener_fecha_hoy_bogota()
    })
