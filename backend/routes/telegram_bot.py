# ===================================
# telegram_bot.py - Bot Didasko V2.0
# ===================================
# MEJORAS V2.0:
# - Siempre publica algo relevante
# - Sistema de 3 niveles de respaldo
# - Busca partidos en próximos días si hoy no hay
# - Publica noticias deportivas si no hay partidos
# ===================================

import os
import requests
import feedparser
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from supabase_client import get_client

telegram_bp = Blueprint('telegram', __name__)

# ===================================
# CONFIGURACIÓN
# ===================================

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHANNEL = '@DidaskoDeportes'
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
DIDASKO_URL = 'https://didasko-ai.onrender.com'

# ===================================
# 📰 NOTICIAS RSS
# ===================================

RSS_FEEDS = {
    'LaLiga': 'https://e00-marca.uecdn.es/rss/futbol/primera-division.xml',
    'Premier League': 'https://www.marca.com/rss/futbol/premier-league.xml',
    'Serie A': 'https://www.marca.com/rss/futbol/serie-a.xml',
    'Bundesliga': 'https://www.marca.com/rss/futbol/bundesliga.xml',
    'Ligue 1': 'https://www.marca.com/rss/futbol/ligue-1.xml',
    'Champions League': 'https://www.marca.com/rss/futbol/champions-league.xml',
    'default': 'https://e00-marca.uecdn.es/rss/futbol.xml'
}

FRASES_MOTIVACIONALES = [
    "⚽ El fútbol es más que un deporte, es pasión pura.",
    "🏆 Los grandes campeones se forjan en los momentos difíciles.",
    "🔥 Cada partido es una oportunidad para hacer historia.",
    "💪 El talento gana partidos, el trabajo en equipo gana campeonatos.",
    "🎯 En el fútbol, como en la vida, cada segundo cuenta.",
    "⭐ Los sueños se cumplen con esfuerzo y dedicación.",
    "🦉 Con inteligencia artificial, todo es posible."
]

# ===================================
# 🎯 FUNCIONES AUXILIARES
# ===================================

def enviar_mensaje_telegram(texto, canal=TELEGRAM_CHANNEL):
    """Envía un mensaje al canal de Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        return {'success': False, 'error': 'Token no configurado'}
    
    try:
        url = f"{TELEGRAM_API}/sendMessage"
        payload = {
            'chat_id': canal,
            'text': texto,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False
        }
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return {'success': True, 'data': response.json()}
        else:
            return {'success': False, 'error': f'Código {response.status_code}', 'detalle': response.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def obtener_noticias_liga(liga_nombre, limite=3):
    """Obtiene las últimas noticias de una liga desde RSS."""
    try:
        feed_url = RSS_FEEDS.get(liga_nombre, RSS_FEEDS['default'])
        feed = feedparser.parse(feed_url)
        
        noticias = []
        for entry in feed.entries[:limite]:
            titulo = entry.get('title', '').strip()
            if titulo:
                noticias.append(f"• {titulo}")
        return noticias
    except Exception as e:
        print(f"⚠️ Error obteniendo noticias: {e}")
        return []


def obtener_noticias_generales(limite=5):
    """Obtiene noticias deportivas generales."""
    try:
        feed = feedparser.parse(RSS_FEEDS['default'])
        noticias = []
        for entry in feed.entries[:limite]:
            titulo = entry.get('title', '').strip()
            link = entry.get('link', '')
            if titulo:
                if link:
                    noticias.append(f"• <a href='{link}'>{titulo}</a>")
                else:
                    noticias.append(f"• {titulo}")
        return noticias
    except Exception as e:
        print(f"⚠️ Error noticias generales: {e}")
        return []


def buscar_partidos_dia(fecha_str):
    """Busca partidos en una fecha específica desde TheSportsDB."""
    try:
        # API pública de TheSportsDB
        url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={fecha_str}&s=Soccer"
        response = requests.get(url, timeout=15)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        eventos = data.get('events', [])
        return eventos if eventos else []
    except Exception as e:
        print(f"⚠️ Error buscando partidos {fecha_str}: {e}")
        return []


def elegir_mejor_partido(partidos):
    """De una lista de partidos, elige el más importante por prioridad."""
    if not partidos:
        return None
    
    prioridades = [
        'UEFA Champions League',
        'UEFA Europa League',
        'LaLiga', 'Spanish La Liga', 'Spanish La Liga',
        'Premier League', 'English Premier League',
        'Serie A', 'Italian Serie A',
        'Bundesliga', 'German Bundesliga',
        'Copa Libertadores',
        'Ligue 1', 'French Ligue 1',
        'Copa Sudamericana',
        'Colombia Categoría Primera A',
        'Copa BetPlay',
        'Brazilian Serie A',
        'Argentine Primera División'
    ]
    
    # Buscar por prioridad
    for liga_prio in prioridades:
        for partido in partidos:
            liga = partido.get('strLeague', '')
            if liga_prio.lower() in liga.lower():
                return partido
    
    # Si no hay prioritario, devolver el primero
    return partidos[0]


def buscar_mejor_partido_disponible():
    """
    Sistema de 3 niveles:
    1. Partido de hoy
    2. Partido de mañana
    3. Partido de pasado mañana
    Devuelve (partido, dias_desde_hoy) o (None, -1)
    """
    hoy = datetime.now()
    
    for dias_adelante in range(0, 4):  # hoy, +1, +2, +3
        fecha = hoy + timedelta(days=dias_adelante)
        fecha_str = fecha.strftime('%Y-%m-%d')
        
        print(f"🔍 Buscando partidos para: {fecha_str}")
        partidos = buscar_partidos_dia(fecha_str)
        
        if partidos:
            mejor = elegir_mejor_partido(partidos)
            if mejor:
                print(f"✅ Encontrado: {mejor.get('strEvent')} en {fecha_str}")
                return (mejor, dias_adelante)
    
    return (None, -1)


def buscar_prediccion_cache(evento_id):
    """Busca predicción en cache de Supabase."""
    try:
        client = get_client()
        if not client:
            return None
        
        result = client.table('predicciones').select('*').eq('partido_id', str(evento_id)).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception as e:
        print(f"⚠️ Error cache predicción: {e}")
        return None


# ===================================
# 📝 FORMATEADORES DE MENSAJE
# ===================================

def formatear_publicacion_partido(partido, prediccion, noticias, dias_adelante=0):
    """Crea el mensaje HTML para publicar un partido."""
    
    equipo_local = partido.get('strHomeTeam', 'Local')
    equipo_visitante = partido.get('strAwayTeam', 'Visitante')
    liga = partido.get('strLeague', 'Fútbol')
    hora = partido.get('strTime', '')[:5] if partido.get('strTime') else '??:??'
    estadio = partido.get('strVenue', '')
    fecha_partido = partido.get('dateEvent', '')
    
    # Determinar título según cuándo se juega
    if dias_adelante == 0:
        titulo = "🔮 <b>PREDICCIÓN DEL DÍA</b>"
        fecha_txt = "📅 HOY"
    elif dias_adelante == 1:
        titulo = "⚽ <b>PARTIDO DESTACADO - MAÑANA</b>"
        fecha_txt = "📅 MAÑANA"
    else:
        titulo = "⚽ <b>PARTIDO DESTACADO PRÓXIMO</b>"
        fecha_txt = f"📅 {fecha_partido}"
    
    mensaje = f"{titulo}\n"
    mensaje += f"{fecha_txt}\n\n"
    mensaje += f"⚽ <b>{equipo_local}</b> vs <b>{equipo_visitante}</b>\n"
    mensaje += f"🏆 {liga}\n"
    mensaje += f"🕒 Hora: {hora}\n"
    
    if estadio:
        mensaje += f"🏟️ {estadio}\n"
    
    mensaje += "\n"
    
    # Predicción IA (si existe)
    if prediccion and prediccion.get('prediccion_texto'):
        mensaje += "━━━━━━━━━━━━━━━\n"
        mensaje += f"🎯 <b>Ganador probable:</b> {prediccion.get('ganador_predicho', 'N/A')}\n"
        mensaje += f"📊 <b>Confianza:</b> {prediccion.get('confianza', 60)}%\n"
        mensaje += "━━━━━━━━━━━━━━━\n\n"
    else:
        mensaje += "🔮 <i>Obtén la predicción IA completa en Didasko AI</i>\n\n"
    
    # Noticias
    if noticias:
        mensaje += f"📰 <b>ÚLTIMAS NOTICIAS:</b>\n"
        for noticia in noticias:
            mensaje += f"{noticia}\n"
        mensaje += "\n"
    
    # Call to action
    mensaje += "━━━━━━━━━━━━━━━\n"
    mensaje += "🦉 <b>¿Quieres predicciones ilimitadas?</b>\n"
    mensaje += f"👉 <a href='{DIDASKO_URL}'>didasko-ai.onrender.com</a>\n\n"
    mensaje += "#DidaskoAI #Futbol #Predicciones ⚽🔮"
    
    return mensaje


def formatear_publicacion_solo_noticias(noticias):
    """Cuando no hay partidos disponibles, publica noticias del día."""
    import random
    frase = random.choice(FRASES_MOTIVACIONALES)
    fecha_hoy = datetime.now().strftime('%d/%m/%Y')
    
    mensaje = "🦉 <b>DIDASKO DEPORTES</b>\n"
    mensaje += f"📅 {fecha_hoy}\n\n"
    mensaje += f"{frase}\n\n"
    
    if noticias:
        mensaje += "📰 <b>NOTICIAS DEPORTIVAS DEL DÍA:</b>\n\n"
        for noticia in noticias:
            mensaje += f"{noticia}\n\n"
    
    mensaje += "━━━━━━━━━━━━━━━\n"
    mensaje += "🦉 <b>Visita Didasko AI:</b>\n"
    mensaje += "🔮 Predicciones IA con NVIDIA\n"
    mensaje += "⚽ Análisis de partidos\n"
    mensaje += "🏆 Todas las ligas del mundo\n\n"
    mensaje += f"👉 <a href='{DIDASKO_URL}'>didasko-ai.onrender.com</a>\n\n"
    mensaje += "#DidaskoAI #Futbol #Deportes ⚽🔮"
    
    return mensaje


# ===================================
# 🎯 ENDPOINT PRINCIPAL
# ===================================

@telegram_bp.route('/publicar-prediccion-diaria', methods=['GET', 'POST'])
def publicar_prediccion_diaria():
    """
    Publica contenido diario con sistema de 3 niveles:
    1. Partido de hoy con predicción
    2. Partido próximo (mañana, +2, +3 días)
    3. Noticias deportivas del día
    """
    try:
        if not TELEGRAM_BOT_TOKEN:
            return jsonify({
                'success': False,
                'error': 'TELEGRAM_BOT_TOKEN no configurado en Render'
            }), 500
        
        # NIVEL 1 y 2: Buscar mejor partido disponible (hoy o próximos días)
        partido, dias_adelante = buscar_mejor_partido_disponible()
        
        if partido:
            # ✅ Hay partido disponible
            evento_id = partido.get('idEvent')
            prediccion = buscar_prediccion_cache(evento_id)
            liga = partido.get('strLeague', 'default')
            noticias = obtener_noticias_liga(liga, limite=3)
            
            mensaje = formatear_publicacion_partido(partido, prediccion, noticias, dias_adelante)
            resultado = enviar_mensaje_telegram(mensaje)
            
            return jsonify({
                'success': resultado['success'],
                'nivel': 1 if dias_adelante == 0 else 2,
                'partido': f"{partido.get('strHomeTeam')} vs {partido.get('strAwayTeam')}",
                'liga': liga,
                'dias_adelante': dias_adelante,
                'con_prediccion': prediccion is not None,
                'noticias_incluidas': len(noticias),
                'telegram_response': resultado
            })
        
        # NIVEL 3: No hay partidos - Publicar solo noticias
        print("⚠️ No hay partidos disponibles - Publicando noticias generales")
        noticias = obtener_noticias_generales(limite=5)
        
        mensaje = formatear_publicacion_solo_noticias(noticias)
        resultado = enviar_mensaje_telegram(mensaje)
        
        return jsonify({
            'success': resultado['success'],
            'nivel': 3,
            'mensaje': 'Publicado con noticias generales',
            'noticias_incluidas': len(noticias),
            'telegram_response': resultado
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }), 500


# ===================================
# 🧪 ENDPOINTS DE PRUEBA
# ===================================

@telegram_bp.route('/test', methods=['GET'])
def test():
    """Endpoint de prueba del bot."""
    try:
        response = requests.get(f"{TELEGRAM_API}/getMe", timeout=5)
        bot_ok = response.status_code == 200
        bot_info = response.json() if bot_ok else None
    except:
        bot_ok = False
        bot_info = None
    
    return jsonify({
        'status': 'ok',
        'endpoint': 'telegram',
        'version': 'V2.0',
        'token_configurado': bool(TELEGRAM_BOT_TOKEN),
        'bot_activo': bot_ok,
        'bot_info': bot_info,
        'canal': TELEGRAM_CHANNEL,
        'endpoints': [
            '/api/telegram/test',
            '/api/telegram/enviar-prueba',
            '/api/telegram/publicar-prediccion-diaria',
            '/api/telegram/diagnostico'
        ]
    })


@telegram_bp.route('/enviar-prueba', methods=['GET'])
def enviar_prueba():
    """Envía un mensaje de prueba al canal."""
    try:
        mensaje = "🦉 <b>Test desde Didasko AI V2.0</b>\n\n"
        mensaje += "✅ El bot está funcionando correctamente\n"
        mensaje += "⚽ Sistema mejorado activado\n\n"
        mensaje += f"🕒 Enviado: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        mensaje += f"👉 <a href='{DIDASKO_URL}'>didasko-ai.onrender.com</a>"
        
        resultado = enviar_mensaje_telegram(mensaje)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@telegram_bp.route('/diagnostico', methods=['GET'])
def diagnostico():
    """Diagnostica qué partidos hay disponibles en próximos días."""
    try:
        hoy = datetime.now()
        resultado = {
            'fecha_servidor': hoy.strftime('%Y-%m-%d %H:%M:%S'),
            'dias_analizados': []
        }
        
        for dias in range(0, 4):
            fecha = hoy + timedelta(days=dias)
            fecha_str = fecha.strftime('%Y-%m-%d')
            partidos = buscar_partidos_dia(fecha_str)
            
            mejor = elegir_mejor_partido(partidos) if partidos else None
            
            resultado['dias_analizados'].append({
                'fecha': fecha_str,
                'dias_desde_hoy': dias,
                'total_partidos': len(partidos),
                'mejor_partido': f"{mejor.get('strHomeTeam')} vs {mejor.get('strAwayTeam')} ({mejor.get('strLeague')})" if mejor else None
            })
        
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
