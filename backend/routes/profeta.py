# ===================================
# profeta.py - Profeta Deportivo V2.0
# ===================================
# Agente autónomo de predicciones deportivas
# API: TheSportsDB (gratis)
# Cache: Supabase para eficiencia
# 🆕 V2.0: Banners de liga + múltiples partidos
# ===================================

import os
import requests
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session
from supabase_client import get_client

profeta_bp = Blueprint('profeta', __name__)

# ===================================
# CONFIGURACIÓN
# ===================================

THESPORTSDB_KEY = os.getenv('THESPORTSDB_KEY', '123')
THESPORTSDB_URL = f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_KEY}"

# 🌍 Ligas prioritarias con banners
LIGAS_PRIORITARIAS = {
    'champions': {
        'id': 4480,
        'nombre': 'UEFA Champions League',
        'pais': 'Europa',
        'banner': 'assets/fondos/champions.jpeg'
    },
    'libertadores': {
        'id': 4482,
        'nombre': 'Copa Libertadores',
        'pais': 'Sudamérica',
        'banner': 'assets/fondos/libertadores.jpeg'
    },
    'bundesliga': {
        'id': 4331,
        'nombre': 'Bundesliga',
        'pais': 'Alemania',
        'banner': 'assets/fondos/bundesliga.jpeg'
    },
    'laliga': {
        'id': 4335,
        'nombre': 'LaLiga',
        'pais': 'España',
        'banner': 'assets/fondos/laliga.jpeg'
    },
    'ligue_1': {
        'id': 4334,
        'nombre': 'Ligue 1',
        'pais': 'Francia',
        'banner': 'assets/fondos/ligue-1.jpeg'
    },
    'copa_colombia': {
        'id': 5183,
        'nombre': 'Copa BetPlay',
        'pais': 'Colombia',
        'banner': 'assets/fondos/copa-colombia.jpeg'
    },
    'premier': {
        'id': 4328,
        'nombre': 'Premier League',
        'pais': 'Inglaterra',
        'banner': 'assets/fondos/premier.jpeg'
    },
    'serie_a': {
        'id': 4332,
        'nombre': 'Serie A',
        'pais': 'Italia',
        'banner': 'assets/fondos/serie-a.jpeg'
    },
    'colombia_primera': {
        'id': 4497,
        'nombre': 'Liga BetPlay Dimayor',
        'pais': 'Colombia',
        'banner': 'assets/fondos/colombia-primera.jpeg'
    },
    'sudamericana': {
        'id': 4724,
        'nombre': 'Copa Sudamericana',
        'pais': 'Sudamérica',
        'banner': 'assets/fondos/sudamericana.jpeg'
    },
}

# ===================================
# FUNCIONES DE THESPORTSDB
# ===================================

def obtener_partidos_del_dia(fecha=None):
    """Obtiene todos los partidos de fútbol de una fecha específica."""
    if not fecha:
        fecha = datetime.now().strftime('%Y-%m-%d')
    
    try:
        url = f"{THESPORTSDB_URL}/eventsday.php?d={fecha}&s=Soccer"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            eventos = data.get('events', []) or []
            return {'success': True, 'partidos': eventos, 'total': len(eventos)}
        
        return {'success': False, 'error': f'Código {response.status_code}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def obtener_partidos_liga_multiples(liga_id, dias_atras=15, dias_adelante=15):
    """
    🆕 Obtiene MÚLTIPLES partidos de una liga usando loop de fechas.
    Recorre X días para atrás y adelante para conseguir muchos partidos.
    """
    partidos_encontrados = []
    hoy = datetime.now()
    
    # Recorrer días hacia atrás
    for i in range(1, dias_atras + 1):
        fecha = (hoy - timedelta(days=i)).strftime('%Y-%m-%d')
        resultado = obtener_partidos_del_dia(fecha)
        if resultado['success']:
            for p in resultado['partidos']:
                if str(p.get('idLeague', '')) == str(liga_id):
                    partidos_encontrados.append(p)
    
    return partidos_encontrados


def obtener_partidos_liga_pasados(liga_id):
    """Obtiene los últimos partidos jugados de una liga (método original + fallback)."""
    try:
        # Intentar método original primero
        url = f"{THESPORTSDB_URL}/eventspastleague.php?id={liga_id}"
        response = requests.get(url, timeout=10)
        
        partidos = []
        if response.status_code == 200:
            data = response.json()
            partidos = data.get('events', []) or []
        
        # 🆕 Si trae pocos, complementar con búsqueda por fechas
        if len(partidos) < 5:
            adicionales = obtener_partidos_liga_multiples(liga_id, dias_atras=15, dias_adelante=0)
            # Combinar sin duplicados
            ids_existentes = {p.get('idEvent') for p in partidos}
            for p in adicionales:
                if p.get('idEvent') not in ids_existentes:
                    partidos.append(p)
                    ids_existentes.add(p.get('idEvent'))
        
        return {'success': True, 'partidos': partidos, 'total': len(partidos)}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def obtener_partidos_liga_proximos(liga_id):
    """Obtiene los próximos partidos de una liga."""
    try:
        url = f"{THESPORTSDB_URL}/eventsnextleague.php?id={liga_id}"
        response = requests.get(url, timeout=10)
        
        partidos = []
        if response.status_code == 200:
            data = response.json()
            partidos = data.get('events', []) or []
        
        # 🆕 Si trae pocos, complementar
        if len(partidos) < 5:
            hoy = datetime.now()
            for i in range(1, 15):
                fecha = (hoy + timedelta(days=i)).strftime('%Y-%m-%d')
                resultado = obtener_partidos_del_dia(fecha)
                if resultado['success']:
                    for p in resultado['partidos']:
                        if str(p.get('idLeague', '')) == str(liga_id):
                            if p.get('idEvent') not in {x.get('idEvent') for x in partidos}:
                                partidos.append(p)
        
        return {'success': True, 'partidos': partidos, 'total': len(partidos)}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def obtener_detalles_partido(evento_id):
    """Obtiene detalles completos de un partido específico."""
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
    """Obtiene los últimos 5 partidos de un equipo (para análisis)."""
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
# CACHE EN SUPABASE
# ===================================

def guardar_partido_cache(partido_data):
    """Guarda o actualiza un partido en Supabase."""
    try:
        client = get_client()
        if not client:
            return
        
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
# 🎯 ENDPOINTS PÚBLICOS
# ===================================

@profeta_bp.route('/hoy', methods=['GET'])
def partidos_hoy():
    """Devuelve los partidos importantes del día."""
    try:
        resultado = obtener_partidos_del_dia()
        
        if not resultado['success']:
            return jsonify(resultado), 500
        
        ids_prioritarios = [str(liga['id']) for liga in LIGAS_PRIORITARIAS.values()]
        partidos_filtrados = [
            p for p in resultado['partidos']
            if str(p.get('idLeague', '')) in ids_prioritarios
        ]
        
        for partido in partidos_filtrados:
            guardar_partido_cache(partido)
        
        return jsonify({
            'success': True,
            'fecha': datetime.now().strftime('%Y-%m-%d'),
            'total_todos': resultado['total'],
            'total_prioritarios': len(partidos_filtrados),
            'partidos': partidos_filtrados
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@profeta_bp.route('/liga/<liga_key>/pasados', methods=['GET'])
def partidos_liga_pasados(liga_key):
    """Devuelve últimos partidos de una liga."""
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
    """Devuelve próximos partidos de una liga."""
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
    """Devuelve detalles completos de un partido."""
    try:
        resultado = obtener_detalles_partido(evento_id)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@profeta_bp.route('/ligas', methods=['GET'])
def listar_ligas():
    """Devuelve todas las ligas prioritarias."""
    return jsonify({
        'success': True,
        'total': len(LIGAS_PRIORITARIAS),
        'ligas': LIGAS_PRIORITARIAS
    })


@profeta_bp.route('/test', methods=['GET'])
def test():
    """Endpoint de prueba."""
    try:
        response = requests.get(f"{THESPORTSDB_URL}/lookupteam.php?id=137617", timeout=5)
        api_ok = response.status_code == 200
    except:
        api_ok = False
    
    return jsonify({
        'status': 'ok',
        'endpoint': 'profeta',
        'thesportsdb_key': THESPORTSDB_KEY,
        'api_conectada': api_ok,
        'ligas_configuradas': len(LIGAS_PRIORITARIAS),
        'message': '⚽ Profeta Deportivo V2.0 - Banners + Multi-partidos'
    })
