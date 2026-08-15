# ===================================
# telegram_bot.py - Bot Didasko V2.2
# ===================================
# MEJORAS V2.2:
# - Predicción IA al vuelo si no hay cache
# - Sistema de 3 niveles de respaldo
# - Endpoint de anuncio comercial diario
# ===================================

import os
import requests
import feedparser
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from supabase_client import get_client

# 🆕 Importar funciones del profeta para generar predicciones
from routes.profeta import (
    obtener_detalles_partido,
    obtener_ultimos_partidos_equipo,
    generar_prediccion_nvidia,
    guardar_prediccion_cache,
    obtener_prediccion_cache
)

telegram_bp = Blueprint('telegram', __name__)

# ===================================
# CONFIGURACIÓN
# ===================================

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHANNEL = '@DidaskoDeportes'
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
DIDASKO_URL = 'https://didasko-ai.onrender.com'
WHATSAPP_NUMERO = '573171547065'
WHATSAPP_DISPLAY = '+57 317 154 7065'

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
        response = requests.post(url, json=payload, timeout=15)
        
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
        'LaLiga', 'Spanish La Liga',
        'Premier League', 'English Premier League',
        'Serie A', 'Italian Serie A',
        'Bundesliga', 'German Bundesliga',
        'Copa Libertadores',
        'Ligue 1', 'French Ligue 1',
        'Copa Sudamericana',
        'Colombia Categoría Primera A',
        'Copa BetPlay',
        'Brazilian Serie A',
        'Argentinian Primera Division',
        'American USL Championship',
        'American Major League Soccer',
        'Mexican Primera Division'
    ]
    
    for liga_prio in prioridades:
        for partido in partidos:
            liga = partido.get('strLeague', '')
            if liga_prio.lower() in liga.lower():
                return partido
    
    return partidos[0]


def buscar_mejor_partido_disponible():
    """Busca el mejor partido en próximos 4 días."""
    hoy = datetime.now()
    
    for dias_adelante in range(0, 4):
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


def obtener_o_generar_prediccion(partido):
    """Busca en cache o genera nueva predicción con IA al vuelo."""
    try:
        evento_id = partido.get('idEvent')
        
        # 1. Buscar en cache
        cache = obtener_prediccion_cache(evento_id)
        if cache:
            print(f"✅ Predicción encontrada en cache")
            return {
                'success': True,
                'prediccion': cache.get('prediccion_texto', ''),
                'ganador': cache.get('ganador_predicho', ''),
                'confianza': cache.get('confianza', 60),
                'desde_cache': True
            }
        
        # 2. Generar nueva con IA
        print(f"🤖 Generando predicción con NVIDIA IA...")
        
        id_local = partido.get('idHomeTeam')
        id_visitante = partido.get('idAwayTeam')
        
        forma_local = obtener_ultimos_partidos_equipo(id_local) if id_local else {'success': False, 'partidos': []}
        forma_visitante = obtener_ultimos_partidos_equipo(id_visitante) if id_visitante else {'success': False, 'partidos': []}
        
        prediccion = generar_prediccion_nvidia(partido, forma_local, forma_visitante)
        
        if prediccion.get('success'):
            guardar_prediccion_cache(partido, prediccion)
            print(f"✅ Predicción generada y cacheada")
            return {
                'success': True,
                'prediccion': prediccion.get('prediccion', ''),
                'ganador': prediccion.get('ganador', ''),
                'confianza': prediccion.get('confianza', 60),
                'desde_cache': False
            }
        
        print(f"⚠️ Error generando predicción: {prediccion.get('error')}")
        return {'success': False, 'error': prediccion.get('error')}
        
    except Exception as e:
        print(f"❌ Error obtener_o_generar_prediccion: {e}")
        return {'success': False, 'error': str(e)}


def extraer_resumen_prediccion(texto_completo, max_lineas=6):
    """Extrae y limpia el texto de la predicción IA."""
    if not texto_completo:
        return ""
    
    texto = texto_completo.replace('**', '')
    texto = texto.replace('* ', '• ')
    
    return texto.strip()


# ===================================
# 📝 FORMATEADORES DE MENSAJE
# ===================================

def formatear_publicacion_partido(partido, prediccion_data, noticias, dias_adelante=0):
    """Crea el mensaje HTML para publicar un partido con predicción IA."""
    
    equipo_local = partido.get('strHomeTeam', 'Local')
    equipo_visitante = partido.get('strAwayTeam', 'Visitante')
    liga = partido.get('strLeague', 'Fútbol')
    hora = partido.get('strTime', '')[:5] if partido.get('strTime') else '??:??'
    estadio = partido.get('strVenue', '')
    fecha_partido = partido.get('dateEvent', '')
    
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
    
    if prediccion_data and prediccion_data.get('success') and prediccion_data.get('prediccion'):
        mensaje += "━━━━━━━━━━━━━━━\n"
        mensaje += "🤖 <b>ANÁLISIS IA (NVIDIA):</b>\n\n"
        
        texto_pred = extraer_resumen_prediccion(prediccion_data.get('prediccion', ''))
        mensaje += f"{texto_pred}\n"
        mensaje += "━━━━━━━━━━━━━━━\n\n"
    else:
        mensaje += "🔮 <i>Obtén la predicción IA en Didasko AI</i>\n\n"
    
    if noticias:
        mensaje += f"📰 <b>ÚLTIMAS NOTICIAS:</b>\n"
        for noticia in noticias:
            mensaje += f"{noticia}\n"
        mensaje += "\n"
    
    mensaje += "━━━━━━━━━━━━━━━\n"
    mensaje += "🦉 <b>¿Quieres predicciones ilimitadas?</b>\n"
    mensaje += f"👉 <a href='{DIDASKO_URL}'>didasko-ai.onrender.com</a>\n\n"
    mensaje += "#DidaskoAI #Futbol #Predicciones ⚽🔮"
    
    if len(mensaje) > 4000:
        mensaje = mensaje[:3950] + "\n\n... (continúa en la web)"
    
    return mensaje


def formatear_publicacion_solo_noticias(noticias):
    """Cuando no hay partidos, publica noticias del día."""
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
# 🎯 ENDPOINT PRINCIPAL - PREDICCIÓN
# ===================================

@telegram_bp.route('/publicar-prediccion-diaria', methods=['GET', 'POST'])
def publicar_prediccion_diaria():
    """Publica predicción del día con IA."""
    try:
        if not TELEGRAM_BOT_TOKEN:
            return jsonify({
                'success': False,
                'error': 'TELEGRAM_BOT_TOKEN no configurado en Render'
            }), 500
        
        partido, dias_adelante = buscar_mejor_partido_disponible()
        
        if partido:
            print(f"⚽ Partido encontrado: {partido.get('strEvent')}")
            
            prediccion_data = obtener_o_generar_prediccion(partido)
            
            liga = partido.get('strLeague', 'default')
            noticias = obtener_noticias_liga(liga, limite=3)
            
            mensaje = formatear_publicacion_partido(partido, prediccion_data, noticias, dias_adelante)
            resultado = enviar_mensaje_telegram(mensaje)
            
            return jsonify({
                'success': resultado['success'],
                'nivel': 1 if dias_adelante == 0 else 2,
                'partido': f"{partido.get('strHomeTeam')} vs {partido.get('strAwayTeam')}",
                'liga': liga,
                'dias_adelante': dias_adelante,
                'prediccion_generada': prediccion_data.get('success', False),
                'desde_cache': prediccion_data.get('desde_cache', False),
                'noticias_incluidas': len(noticias),
                'longitud_mensaje': len(mensaje),
                'telegram_response': resultado
            })
        
        print("⚠️ No hay partidos disponibles - Publicando noticias")
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
# 📢 ENDPOINT DE ANUNCIO COMERCIAL
# ===================================

@telegram_bp.route('/publicar-anuncio', methods=['GET', 'POST'])
def publicar_anuncio():
    """Publica anuncio comercial diario (12 PM)."""
    try:
        if not TELEGRAM_BOT_TOKEN:
            return jsonify({
                'success': False,
                'error': 'TELEGRAM_BOT_TOKEN no configurado'
            }), 500
        
        fecha_hoy = datetime.now().strftime('%d/%m/%Y')
        
        mensaje = "📢 <b>ESPACIO PUBLICITARIO DISPONIBLE</b>\n\n"
        mensaje += "🎯 <b>¿Quieres publicar aquí?</b>\n\n"
        mensaje += "🦉 Llega a nuestra audiencia deportiva con:\n"
        mensaje += "✅ Publicaciones diarias\n"
        mensaje += "✅ Contenido de calidad\n"
        mensaje += "✅ Audiencia comprometida\n"
        mensaje += "✅ Precios accesibles\n\n"
        mensaje += "━━━━━━━━━━━━━━━\n"
        mensaje += "📱 <b>Contáctanos:</b>\n"
        mensaje += f"📞 WhatsApp: <a href='https://wa.me/{WHATSAPP_NUMERO}'>{WHATSAPP_DISPLAY}</a>\n"
        mensaje += f"🌐 Web: <a href='{DIDASKO_URL}'>didasko-ai.onrender.com</a>\n"
        mensaje += "━━━━━━━━━━━━━━━\n\n"
        mensaje += "🚀 <i>Impulsa tu marca con Didasko Deportes</i>\n\n"
        mensaje += "#Publicidad #DidaskoAI #Deportes #Marketing"
        
        resultado = enviar_mensaje_telegram(mensaje)
        
        return jsonify({
            'success': resultado['success'],
            'tipo': 'anuncio_comercial',
            'fecha': fecha_hoy,
            'telegram_response': resultado
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
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
        'version': 'V2.2 - Con anuncio comercial',
        'token_configurado': bool(TELEGRAM_BOT_TOKEN),
        'bot_activo': bot_ok,
        'bot_info': bot_info,
        'canal': TELEGRAM_CHANNEL,
        'endpoints': [
            '/api/telegram/test',
            '/api/telegram/enviar-prueba',
            '/api/telegram/publicar-prediccion-diaria',
            '/api/telegram/publicar-anuncio',
            '/api/telegram/diagnostico'
        ]
    })


@telegram_bp.route('/enviar-prueba', methods=['GET'])
def enviar_prueba():
    """Envía un mensaje de prueba al canal."""
    try:
        mensaje = "🦉 <b>Test desde Didasko AI V2.2</b>\n\n"
        mensaje += "✅ Bot funcionando con IA integrada\n"
        mensaje += "🤖 NVIDIA Llama activo\n"
        mensaje += "📢 Sistema de anuncios listo\n\n"
        mensaje += f"🕒 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        mensaje += f"👉 <a href='{DIDASKO_URL}'>didasko-ai.onrender.com</a>"
        
        resultado = enviar_mensaje_telegram(mensaje)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@telegram_bp.route('/diagnostico', methods=['GET'])
def diagnostico():
    """Diagnostica qué partidos hay disponibles."""
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
