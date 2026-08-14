# ===================================
# telegram_bot.py - Bot Didasko V1.0
# ===================================
# Bot Telegram para publicar en @DidaskoDeportes
# - Publica 1 predicción al día a las 8 AM
# - Incluye noticias RSS de fútbol
# - No interfiere con el sitio web
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

# URL del sitio web (para el link en las publicaciones)
DIDASKO_URL = 'https://didasko-ai.onrender.com'

# ===================================
# 📰 NOTICIAS RSS POR LIGA
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

# ===================================
# 🎯 FUNCIONES PRINCIPALES
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
        # Buscar el feed más apropiado
        feed_url = RSS_FEEDS.get(liga_nombre, RSS_FEEDS['default'])
        
        # Parsear el RSS
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


def elegir_partido_destacado():
    """Elige el partido más importante del día desde el Profeta."""
    try:
        # Llamar al endpoint interno del Profeta
        response = requests.get(f"{DIDASKO_URL}/api/profeta/hoy", timeout=15)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        if not data.get('success') or not data.get('partidos'):
            return None
        
        partidos = data['partidos']
        
        # Prioridad de ligas (más importante primero)
        prioridades = [
            'UEFA Champions League',
            'LaLiga', 'Spanish La Liga',
            'Premier League', 'English Premier League',
            'Serie A', 'Italian Serie A',
            'Bundesliga', 'German Bundesliga',
            'Copa Libertadores',
            'Ligue 1', 'French Ligue 1',
            'Copa Sudamericana',
            'Colombia Categoría Primera A',
            'Copa BetPlay'
        ]
        
        # Buscar el partido de la liga más prioritaria
        for liga_prio in prioridades:
            for partido in partidos:
                if liga_prio.lower() in partido.get('strLeague', '').lower():
                    return partido
        
        # Si no hay ninguno prioritario, devolver el primero
        return partidos[0] if partidos else None
        
    except Exception as e:
        print(f"⚠️ Error eligiendo partido: {e}")
        return None


def generar_prediccion_para_partido(evento_id):
    """Llama al endpoint interno para generar la predicción IA."""
    try:
        # NOTA: Este endpoint requiere sesión, así que usaremos directamente Supabase
        client = get_client()
        if not client:
            return None
        
        # Buscar en cache primero
        result = client.table('predicciones').select('*').eq('partido_id', str(evento_id)).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        
        return None
    except Exception as e:
        print(f"⚠️ Error generando predicción: {e}")
        return None


def formatear_publicacion(partido, prediccion, noticias):
    """Crea el mensaje HTML formateado para Telegram."""
    fecha_hoy = datetime.now().strftime('%d de %B de %Y')
    
    equipo_local = partido.get('strHomeTeam', 'Local')
    equipo_visitante = partido.get('strAwayTeam', 'Visitante')
    liga = partido.get('strLeague', 'Liga')
    hora = partido.get('strTime', '')[:5] if partido.get('strTime') else '??:??'
    estadio = partido.get('strVenue', '')
    
    # Construir el mensaje
    mensaje = f"🔮 <b>PREDICCIÓN DEL DÍA</b>\n"
    mensaje += f"📅 {fecha_hoy}\n\n"
    mensaje += f"⚽ <b>{equipo_local}</b> vs <b>{equipo_visitante}</b>\n"
    mensaje += f"🏆 {liga}\n"
    mensaje += f"🕒 Hora: {hora}\n"
    
    if estadio:
        mensaje += f"🏟️ {estadio}\n"
    
    mensaje += "\n"
    
    # Predicción IA
    if prediccion and prediccion.get('prediccion_texto'):
        mensaje += "━━━━━━━━━━━━━━━\n"
        mensaje += f"🎯 <b>Ganador probable:</b> {prediccion.get('ganador_predicho', 'N/A')}\n"
        mensaje += f"📊 <b>Confianza:</b> {prediccion.get('confianza', 60)}%\n"
        mensaje += "━━━━━━━━━━━━━━━\n\n"
    else:
        mensaje += "🔮 <i>Genera la predicción completa en Didasko AI</i>\n\n"
    
    # Noticias
    if noticias:
        mensaje += f"📰 <b>NOTICIAS DE {liga.upper()}:</b>\n"
        for noticia in noticias:
            mensaje += f"{noticia}\n"
        mensaje += "\n"
    
    # Call to action
    mensaje += "━━━━━━━━━━━━━━━\n"
    mensaje += "🦉 <b>¿Quieres predicciones ilimitadas?</b>\n"
    mensaje += f"👉 <a href='{DIDASKO_URL}'>didasko-ai.onrender.com</a>\n\n"
    mensaje += "#DidaskoAI #Futbol #Predicciones ⚽🔮"
    
    return mensaje


# ===================================
# 🎯 ENDPOINT PARA PUBLICAR
# ===================================

@telegram_bp.route('/publicar-prediccion-diaria', methods=['GET', 'POST'])
def publicar_prediccion_diaria():
    """
    Endpoint que publica la predicción del día en el canal.
    Se llama automáticamente cada día a las 8 AM.
    """
    try:
        # Verificar que hay token
        if not TELEGRAM_BOT_TOKEN:
            return jsonify({
                'success': False,
                'error': 'TELEGRAM_BOT_TOKEN no configurado en Render'
            }), 500
        
        # 1. Elegir partido destacado del día
        partido = elegir_partido_destacado()
        
        if not partido:
            # No hay partidos hoy, publicar mensaje alternativo
            mensaje = "🦉 <b>DIDASKO DEPORTES</b>\n\n"
            mensaje += "📅 Hoy no hay partidos destacados de las ligas prioritarias.\n\n"
            mensaje += "⚽ Visita Didasko AI para ver partidos de otras ligas:\n"
            mensaje += f"👉 <a href='{DIDASKO_URL}'>didasko-ai.onrender.com</a>\n\n"
            mensaje += "#DidaskoAI #Futbol"
            
            resultado = enviar_mensaje_telegram(mensaje)
            return jsonify({
                'success': True,
                'mensaje': 'Publicado mensaje alternativo (sin partidos)',
                'telegram_response': resultado
            })
        
        # 2. Buscar predicción cacheada
        evento_id = partido.get('idEvent')
        prediccion = generar_prediccion_para_partido(evento_id)
        
        # 3. Obtener noticias de la liga
        liga = partido.get('strLeague', 'default')
        noticias = obtener_noticias_liga(liga, limite=3)
        
        # 4. Formatear mensaje
        mensaje = formatear_publicacion(partido, prediccion, noticias)
        
        # 5. Enviar al canal
        resultado = enviar_mensaje_telegram(mensaje)
        
        return jsonify({
            'success': resultado['success'],
            'partido': f"{partido.get('strHomeTeam')} vs {partido.get('strAwayTeam')}",
            'liga': liga,
            'con_prediccion': prediccion is not None,
            'noticias_incluidas': len(noticias),
            'telegram_response': resultado
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }), 500


# ===================================
# 🧪 ENDPOINT DE PRUEBA
# ===================================

@telegram_bp.route('/test', methods=['GET'])
def test():
    """Endpoint de prueba del bot."""
    try:
        # Verificar token con /getMe
        response = requests.get(f"{TELEGRAM_API}/getMe", timeout=5)
        bot_ok = response.status_code == 200
        bot_info = response.json() if bot_ok else None
    except:
        bot_ok = False
        bot_info = None
    
    return jsonify({
        'status': 'ok',
        'endpoint': 'telegram',
        'version': 'V1.0',
        'token_configurado': bool(TELEGRAM_BOT_TOKEN),
        'bot_activo': bot_ok,
        'bot_info': bot_info,
        'canal': TELEGRAM_CHANNEL,
        'endpoints': [
            '/api/telegram/test',
            '/api/telegram/publicar-prediccion-diaria'
        ]
    })


@telegram_bp.route('/enviar-prueba', methods=['GET'])
def enviar_prueba():
    """Envía un mensaje de prueba al canal."""
    try:
        mensaje = "🦉 <b>Test desde Didasko AI</b>\n\n"
        mensaje += "✅ El bot está funcionando correctamente\n"
        mensaje += "⚽ Pronto empezarán las predicciones diarias\n\n"
        mensaje += f"🕒 Enviado: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        mensaje += f"👉 <a href='{DIDASKO_URL}'>didasko-ai.onrender.com</a>"
        
        resultado = enviar_mensaje_telegram(mensaje)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
