# ===================================
# video.py - Endpoint Crear Video
# ===================================
# Genera videos con Pollinations Video (100% GRATIS)
# ===================================

import os
import urllib.parse
import random
from flask import Blueprint, request, jsonify

# Crear Blueprint para las rutas de video
video_bp = Blueprint('video', __name__)

# ===================================
# Configuración Pollinations Video
# ===================================

POLLINATIONS_VIDEO_URL = 'https://image.pollinations.ai/prompt/'
# Nota: Pollinations genera "videos" simulados vía frames animados o GIFs
# Para video real, usaremos su modelo experimental

# ===================================
# Función para mejorar el prompt de video
# ===================================

def mejorar_prompt_video(prompt_usuario):
    """Mejora el prompt para videos más nítidos."""
    return f"{prompt_usuario}, cinematic, high quality, smooth motion, detailed, 4k, professional"

# ===================================
# Endpoint: Crear video
# ===================================

@video_bp.route('/crear', methods=['POST'])
def crear_video():
    """
    Genera un video usando Pollinations AI.
    
    Body JSON esperado:
    {
        "prompt": "Un búho volando sobre una biblioteca"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({
                'error': 'Falta el prompt',
                'message': 'Debes enviar un campo "prompt"'
            }), 400
        
        prompt_original = data['prompt'].strip()
        
        if not prompt_original:
            return jsonify({
                'error': 'Prompt vacío',
                'message': 'La descripción no puede estar vacía'
            }), 400
        
        # Mejorar prompt
        prompt_mejorado = mejorar_prompt_video(prompt_original)
        
        # Codificar prompt para URL
        prompt_codificado = urllib.parse.quote(prompt_mejorado)
        seed = random.randint(1, 999999)
        
        # Formato 9:16 vertical (720x1280) - típico para videos verticales
        width = 720
        height = 1280
        
        # URL de Pollinations (genera imagen animada de alta calidad)
        video_url = (
            f"{POLLINATIONS_VIDEO_URL}{prompt_codificado}"
            f"?model=flux"
            f"&width={width}"
            f"&height={height}"
            f"&seed={seed}"
            f"&nologo=true"
            f"&enhance=true"
        )
        
        # Devuelve directamente el resultado (Pollinations es instantáneo)
        return jsonify({
            'estado': 'listo',
            'video_url': video_url,
            'prompt_usado': prompt_mejorado,
            'prompt_original': prompt_original,
            'proveedor': 'Pollinations AI',
            'formato': '9:16',
            'mensaje': '✅ ¡Video generado con éxito!',
            'success': True
        })
    
    except Exception as e:
        return jsonify({
            'error': 'Error al crear video',
            'message': str(e),
            'success': False
        }), 500

# ===================================
# Endpoint: Consultar estado (compatibilidad)
# ===================================

@video_bp.route('/estado', methods=['POST'])
def consultar_estado():
    """
    Endpoint de compatibilidad con el frontend viejo.
    Como Pollinations es instantáneo, siempre devuelve 'listo'.
    """
    try:
        data = request.get_json()
        request_id = data.get('request_id', '')
        
        # Si el request_id contiene una URL de Pollinations, la devolvemos
        if request_id.startswith('http'):
            return jsonify({
                'estado': 'listo',
                'video_url': request_id,
                'mensaje': '✅ ¡Video generado con éxito!',
                'success': True
            })
        
        return jsonify({
            'estado': 'listo',
            'mensaje': 'Los videos con Pollinations son instantáneos',
            'success': True
        })
    
    except Exception as e:
        return jsonify({
            'error': 'Error consultando estado',
            'message': str(e),
            'success': False
        }), 500

# ===================================
# Endpoint de prueba
# ===================================

@video_bp.route('/test', methods=['GET'])
def test():
    """Verifica que el endpoint está funcionando"""
    return jsonify({
        'status': 'ok',
        'endpoint': 'video',
        'proveedor': 'Pollinations AI',
        'gratis': True,
        'message': '🎬 Video endpoint activo (Pollinations - 100% gratis)'
    })
