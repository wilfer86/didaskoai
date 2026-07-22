# ===================================
# imagen.py - Endpoint Crear Imagen
# ===================================
# Genera imágenes con SiliconFlow (Flux)
# ===================================

import os
import requests
from flask import Blueprint, request, jsonify

# Crear Blueprint para las rutas de imagen
imagen_bp = Blueprint('imagen', __name__)

# ===================================
# Configuración SiliconFlow
# ===================================

SILICONFLOW_API_KEY = os.getenv('SILICONFLOW_API_KEY')
SILICONFLOW_URL = 'https://api.siliconflow.cn/v1/images/generations'

# Modelo a usar (gratis en SiliconFlow)
# Opciones: 'black-forest-labs/FLUX.1-schnell', 'stabilityai/stable-diffusion-3-medium'
DEFAULT_MODEL = 'black-forest-labs/FLUX.1-schnell'

# ===================================
# Función para mejorar el prompt
# ===================================

def mejorar_prompt(prompt_usuario):
    """
    Agrega palabras clave para mejorar la calidad de la imagen.
    Traduce implícitamente al inglés si viene en español.
    """
    prompt_mejorado = f"{prompt_usuario}, high quality, detailed, professional, 4k"
    return prompt_mejorado

# ===================================
# Endpoint principal
# ===================================

@imagen_bp.route('/crear', methods=['POST'])
def crear_imagen():
    """
    Genera una imagen a partir de un prompt.
    
    Body JSON esperado:
    {
        "prompt": "Un búho sabio sobre una columna griega",
        "size": "1024x1024"  (opcional)
    }
    """
    try:
        # Validar clave API
        if not SILICONFLOW_API_KEY:
            return jsonify({
                'error': 'SILICONFLOW_API_KEY no configurada',
                'message': 'Configura tu clave de SiliconFlow en el archivo .env'
            }), 500
        
        # Obtener datos del request
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({
                'error': 'Falta el prompt',
                'message': 'Debes enviar un campo "prompt" describiendo la imagen'
            }), 400
        
        prompt_original = data['prompt'].strip()
        
        if not prompt_original:
            return jsonify({
                'error': 'Prompt vacío',
                'message': 'La descripción no puede estar vacía'
            }), 400
        
        # Tamaño de la imagen (por defecto cuadrada)
        size = data.get('size', '1024x1024')
        
        # Mejorar el prompt para mejor calidad
        prompt_mejorado = mejorar_prompt(prompt_original)
        
        # Preparar petición a SiliconFlow
        headers = {
            'Authorization': f'Bearer {SILICONFLOW_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': DEFAULT_MODEL,
            'prompt': prompt_mejorado,
            'image_size': size,
            'batch_size': 1,
            'num_inference_steps': 4,  # Flux Schnell usa pocos pasos (rápido)
            'guidance_scale': 3.5
        }
        
        # Hacer petición a SiliconFlow
        response = requests.post(
            SILICONFLOW_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        # Verificar respuesta
        if response.status_code != 200:
            return jsonify({
                'error': 'Error en SiliconFlow',
                'message': f'Código {response.status_code}: {response.text}',
                'success': False
            }), 500
        
        # Extraer URL de la imagen generada
        resultado = response.json()
        
        if 'data' not in resultado or len(resultado['data']) == 0:
            return jsonify({
                'error': 'No se generó imagen',
                'message': 'SiliconFlow no devolvió ninguna imagen',
                'raw_response': resultado
            }), 500
        
        imagen_url = resultado['data'][0].get('url', '')
        
        return jsonify({
            'imagen_url': imagen_url,
            'prompt_usado': prompt_mejorado,
            'prompt_original': prompt_original,
            'modelo': DEFAULT_MODEL,
            'success': True
        })
    
    except requests.exceptions.Timeout:
        return jsonify({
            'error': 'Tiempo de espera agotado',
            'message': 'SiliconFlow tardó demasiado en responder',
            'success': False
        }), 504
    
    except Exception as e:
        return jsonify({
            'error': 'Error al crear imagen',
            'message': str(e),
            'success': False
        }), 500

# ===================================
# Endpoint de prueba
# ===================================

@imagen_bp.route('/test', methods=['GET'])
def test():
    """Verifica que el endpoint de imagen está funcionando"""
    return jsonify({
        'status': 'ok',
        'endpoint': 'imagen',
        'siliconflow_configured': bool(SILICONFLOW_API_KEY),
        'modelo': DEFAULT_MODEL,
        'message': '🎨 Imagen endpoint funcionando'
    })