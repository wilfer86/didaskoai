# ===================================
# video.py - Endpoint Crear Video
# ===================================
# Genera videos con SiliconFlow (CogVideoX)
# Proceso asíncrono: crear → esperar → consultar
# ===================================

import os
import requests
from flask import Blueprint, request, jsonify

# Crear Blueprint para las rutas de video
video_bp = Blueprint('video', __name__)

# ===================================
# Configuración SiliconFlow
# ===================================

SILICONFLOW_API_KEY = os.getenv('SILICONFLOW_API_KEY')
SILICONFLOW_VIDEO_URL = 'https://api.siliconflow.cn/v1/video/submit'
SILICONFLOW_STATUS_URL = 'https://api.siliconflow.cn/v1/video/status'

# Modelo de video (gratis)
DEFAULT_VIDEO_MODEL = 'THUDM/CogVideoX-2b'

# ===================================
# Función para mejorar el prompt de video
# ===================================

def mejorar_prompt_video(prompt_usuario):
    """
    Mejora el prompt para generar videos más nítidos.
    """
    prompt_mejorado = f"{prompt_usuario}, cinematic, high quality, smooth motion, detailed"
    return prompt_mejorado

# ===================================
# Endpoint: Crear video (envía la solicitud)
# ===================================

@video_bp.route('/crear', methods=['POST'])
def crear_video():
    """
    Envía una solicitud para crear un video.
    Devuelve un ID que se usa para consultar el estado.
    
    Body JSON esperado:
    {
        "prompt": "Un búho volando sobre una biblioteca antigua"
    }
    """
    try:
        # Validar clave API
        if not SILICONFLOW_API_KEY:
            return jsonify({
                'error': 'SILICONFLOW_API_KEY no configurada',
                'message': 'Configura tu clave de SiliconFlow en el archivo .env'
            }), 500
        
        # Obtener datos
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({
                'error': 'Falta el prompt',
                'message': 'Debes enviar un campo "prompt" describiendo el video'
            }), 400
        
        prompt_original = data['prompt'].strip()
        
        if not prompt_original:
            return jsonify({
                'error': 'Prompt vacío',
                'message': 'La descripción no puede estar vacía'
            }), 400
        
        # Mejorar prompt
        prompt_mejorado = mejorar_prompt_video(prompt_original)
        
        # Preparar petición
        headers = {
            'Authorization': f'Bearer {SILICONFLOW_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': DEFAULT_VIDEO_MODEL,
            'prompt': prompt_mejorado
        }
        
        # Enviar solicitud a SiliconFlow
        response = requests.post(
            SILICONFLOW_VIDEO_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            return jsonify({
                'error': 'Error en SiliconFlow',
                'message': f'Código {response.status_code}: {response.text}',
                'success': False
            }), 500
        
        resultado = response.json()
        request_id = resultado.get('requestId', '')
        
        if not request_id:
            return jsonify({
                'error': 'No se obtuvo ID de solicitud',
                'message': 'SiliconFlow no devolvió un ID válido',
                'raw_response': resultado
            }), 500
        
        return jsonify({
            'request_id': request_id,
            'prompt_usado': prompt_mejorado,
            'prompt_original': prompt_original,
            'modelo': DEFAULT_VIDEO_MODEL,
            'estado': 'procesando',
            'mensaje': '🎬 Video en proceso. Consulta el estado con /estado',
            'tiempo_estimado': '1-3 minutos',
            'success': True
        })
    
    except requests.exceptions.Timeout:
        return jsonify({
            'error': 'Tiempo agotado',
            'message': 'SiliconFlow tardó demasiado',
            'success': False
        }), 504
    
    except Exception as e:
        return jsonify({
            'error': 'Error al crear video',
            'message': str(e),
            'success': False
        }), 500

# ===================================
# Endpoint: Consultar estado del video
# ===================================

@video_bp.route('/estado', methods=['POST'])
def consultar_estado():
    """
    Consulta si el video ya está listo.
    
    Body JSON esperado:
    {
        "request_id": "abc123xyz"
    }
    """
    try:
        if not SILICONFLOW_API_KEY:
            return jsonify({
                'error': 'SILICONFLOW_API_KEY no configurada'
            }), 500
        
        data = request.get_json()
        request_id = data.get('request_id', '').strip()
        
        if not request_id:
            return jsonify({
                'error': 'Falta request_id',
                'message': 'Debes enviar el ID del video a consultar'
            }), 400
        
        headers = {
            'Authorization': f'Bearer {SILICONFLOW_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {'requestId': request_id}
        
        # Consultar estado
        response = requests.post(
            SILICONFLOW_STATUS_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            return jsonify({
                'error': 'Error consultando estado',
                'message': f'Código {response.status_code}: {response.text}',
                'success': False
            }), 500
        
        resultado = response.json()
        status = resultado.get('status', 'unknown')
        
        # Estados posibles: 'Succeed', 'InQueue', 'InProgress', 'Failed'
        if status == 'Succeed':
            # Video listo
            results = resultado.get('results', {})
            videos = results.get('videos', [])
            
            if videos and len(videos) > 0:
                video_url = videos[0].get('url', '')
                
                return jsonify({
                    'estado': 'listo',
                    'video_url': video_url,
                    'request_id': request_id,
                    'mensaje': '✅ ¡Video generado con éxito!',
                    'success': True
                })
            else:
                return jsonify({
                    'estado': 'error',
                    'mensaje': 'Video completado pero sin URL',
                    'success': False
                })
        
        elif status in ['InQueue', 'InProgress']:
            # Todavía procesando
            return jsonify({
                'estado': 'procesando',
                'request_id': request_id,
                'mensaje': '⏳ Video aún se está generando... espera un momento',
                'status_raw': status,
                'success': True
            })
        
        elif status == 'Failed':
            return jsonify({
                'estado': 'fallido',
                'mensaje': '❌ La generación del video falló',
                'reason': resultado.get('reason', 'Desconocido'),
                'success': False
            })
        
        else:
            return jsonify({
                'estado': 'desconocido',
                'status_raw': status,
                'raw_response': resultado,
                'success': False
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
    """Verifica que el endpoint de video está funcionando"""
    return jsonify({
        'status': 'ok',
        'endpoint': 'video',
        'siliconflow_configured': bool(SILICONFLOW_API_KEY),
        'modelo': DEFAULT_VIDEO_MODEL,
        'message': '🎬 Video endpoint funcionando'
    })