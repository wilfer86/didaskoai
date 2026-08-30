# ===================================
# profeta.py - Profeta Deportivo V3.11 (CORREGIDO - Prioriza Colombia y Fecha Real)
# ===================================
# Agente autónomo de predicciones deportivas
# API: TheSportsDB (gratis)
# IA: Didasko AI (motor Gemini Flash Lite Latest)
# Cache: Supabase para eficiencia
# 🆕 V3.11: Corrige fecha Colombia, prioriza ligas locales SIEMPRE
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

# 🌍 Ligas prioritarias con IDs de TheSportsDB
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

def obtener_fecha_manana_bogota():
    """Devuelve la fecha de MAÑANA en Colombia (YYYY-MM-DD)."""
    tz_bogota = pytz.timezone('America/Bogota')
    manana = datetime.now(tz_bogota) + timedelta(days=1)
    return manana.strftime('%Y-%m-%d')

# ===================================
# FUNCIONES DE THESPORTSDB (OPTIMIZADAS)
# ===================================

def obtener_partidos_del_dia(fecha=None):
    """Obtiene todos los partidos de fútbol de una fecha específica."""
    if not fecha:
        fecha = obtener_fecha_hoy_bogota()
    
    try:
        url = f"{THESPORTSDB_URL}/eventsday.php?d={fecha}&s=Soccer"
        print(f"🔍 Consultando API: {url}")
        response = requests.get(url, timeout=10)
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            eventos = data.get('events', []) or []
            print(f"✅ API devolvió {len(eventos)} partidos para {fecha}")
            
            # Debug: Mostrar IDs de ligas encontradas
            if eventos:
                ids_encontradas = set(p.get('idLeague') for p in eventos if p.get('idLeague'))
                print(f" IDs de ligas encontradas: {ids_encontradas}")
            
            return {'success': True, 'partidos': eventos, 'total': len(eventos), 'fecha': fecha}
        
        if response.status_code == 429:
            return {'success': False, 'error': 'Límite de API alcanzado.', 'partidos': [], 'total': 0, 'fecha': fecha}
        
        return {'success': False, 'error': f'Código {response.status_code}', 'partidos': [], 'total': 0, 'fecha': fecha}
    except Exception as e:
        print(f"❌ Error en API: {str(e)}")
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
