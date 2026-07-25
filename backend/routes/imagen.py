# ===================================
# imagen.py - Endpoint Crear Imagen
# ===================================
# Sistema con respaldo automático:
# 🥇 Primario: Hugging Face (FLUX)
# 🥈 Respaldo: Pollinations AI (100% gratis)
# ===================================

import os
import requests
import urllib.parse
import random
import base64
from flask import Blueprint, request, jsonify

# Crear Blueprint para las rutas de imagen
imagen_bp = Blueprint('imagen', __name__)

# ===================================
# Configuración
# ===================================

HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
HUGGINGFACE_MODEL = 'black-forest-labs/FLUX.1-schnell'
HUGGINGFACE_URL = f'https://router.huggingface.co/hf-inference/models/{HUGGINGFACE_MODEL}'

POLLINATIONS_URL = 'https://image.pollinations.ai/prompt/'
POLLINATIONS_MODEL = 'flux'

# ===================================
# Funciones auxiliares
# ===================================

def mejorar_prompt(prompt_usuario):
    """Agrega palabras clave para mejorar la calidad."""
    return f"{prompt_usuario}, high quality, detailed, professional, 4k, masterpiece"

def formato_a_dimensiones(formato):
    """Convierte formato aspect ratio a width y height."""
    formatos = {
        '1:1': (1024, 1024),
        '16:9': (1280, 720),
        '9:16': (720, 1280)
    }
    return formatos.get(formato, (1024, 1024))

# ===================================
# Proveedor 1: Hugging Face (Primario)
# ===================================

def generar_con_huggingface(prompt, width, height):
    """
    Genera imagen con Hugging Face.
    Devuelve base64 de la imagen o None si falla.
    """
    if not HUGGINGFACE_API_KEY:
        return None, "Hugging Face API Key no configurada"
    
    try:
        headers = {
            'Authorization': f'Bearer {HUGGINGFACE_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'inputs': prompt,
            'parameters': {
                'width': width,
                'height': height,
                'num_inference_steps': 4
            }
        }
        
        response = requests.post(
            HUGGINGFACE_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            # Hugging Face devuelve la imagen como bytes
            imagen_bytes = response.content
            imagen_base64 = base64.b64encode(imagen_bytes).decode('utf-8')
            imagen_url = f"data:image/png;base64,{imagen_base64}"
            return imagen_url, None
        else:
            return None, f"HF Código {response.status_code}: {response.text[:200]}"
    
    except Exception as e:
        return None, f"HF Error: {str(e)}"

# ===================================
# Proveedor 2: Pollinations AI (Respaldo)
# ===================================

def generar_con_pollinations(prompt, width, height):
    """
    Genera imagen con Pollinations AI (100% gratis, sin key).
    Devuelve URL directa de la imagen.
    """
    try:
        prompt_codificado = urllib.parse.quote(prompt)
        seed = random.randint(1, 999999)
        
        imagen_url = (
            f"{POLLINATIONS_URL}{prompt_codificado}"
            f"?model={POLLINATIONS_MODEL}"
            f"&width={width}"
            f"&height={height}"
            f"&seed={seed}"
            f"&nologo=true"
            f"&enhance=true"
        )
        
        return imagen_url, None
    
    except Exception as e:
        return None, f"Pollinations Error: {str(e)}"

# ===================================
# Endpoint principal
# ===================================

@imagen_bp.route('/crear', methods=['POST'])
def crear_imagen():
    """
    Genera una imagen usando Hugging Face como primario y Pollinations como respaldo.
    
    Body JSON esperado:
    {
        "prompt": "Un búho sabio",
        "formato": "1:1"  (opcional: 1:1, 16:9, 9:16)
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
        
        # Formato
        formato = data.get('formato', '1:1')
        width, height = formato_a_dimensiones(formato)
        
        # Mejorar prompt
        prompt_mejorado = mejorar_prompt(prompt_original)
        
        # 🥇 INTENTO 1: Hugging Face
        imagen_url, error_hf = generar_con_huggingface(prompt_mejorado, width, height)
        
        if imagen_url:
            return jsonify({
                'imagen_url': imagen_url,
                'prompt_usado': prompt_mejorado,
                'prompt_original': prompt_original,
                'proveedor': 'Hugging Face',
                'modelo': HUGGINGFACE_MODEL,
                'formato': formato,
                'success': True
            })
        
        # 🥈 INTENTO 2 (RESPALDO): Pollinations AI
        print(f"⚠️ Hugging Face falló: {error_hf}. Usando Pollinations como respaldo.")
        
        imagen_url, error_pol = generar_con_pollinations(prompt_mejorado, width, height)
        
        if imagen_url:
            return jsonify({
                'imagen_url': imagen_url,
                'prompt_usado': prompt_mejorado,
                'prompt_original': prompt_original,
                'proveedor': 'Pollinations AI (respaldo)',
                'modelo': POLLINATIONS_MODEL,
                'formato': formato,
                'success': True,
                'nota_hf': error_hf
            })
        
        # Si ambos fallan
        return jsonify({
            'error': 'Ambos proveedores fallaron',
            'message': f'HF: {error_hf} | Pollinations: {error_pol}',
            'success': False
        }), 500
    
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
    """Verifica que el endpoint está funcionando"""
    return jsonify({
        'status': 'ok',
        'endpoint': 'imagen',
        'proveedor_primario': 'Hugging Face',
        'huggingface_configured': bool(HUGGINGFACE_API_KEY),
        'proveedor_respaldo': 'Pollinations AI',
        'pollinations_disponible': True,
        'modelo_primario': HUGGINGFACE_MODEL,
        'modelo_respaldo': POLLINATIONS_MODEL,
        'message': '🎨 Sistema dual: HF + Pollinations activo'
    })
