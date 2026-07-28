# ===================================
# imagen.py - Endpoint Crear/Editar Imagen
# ===================================
# 🥇 Crear: NVIDIA FLUX.1-schnell
# 🎨 Editar: Pollinations Kontext
# 🥈 Respaldo crear: Hugging Face
# 🥉 Último respaldo: Pollinations AI
# ===================================

import os
import requests
import urllib.parse
import random
import base64
from flask import Blueprint, request, jsonify

imagen_bp = Blueprint('imagen', __name__)

# ===================================
# Configuración
# ===================================

NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY')
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')

NVIDIA_FLUX_URL = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell"

HUGGINGFACE_MODEL = 'stabilityai/stable-diffusion-3.5-large'
HUGGINGFACE_URL = f'https://router.huggingface.co/hf-inference/models/{HUGGINGFACE_MODEL}'

POLLINATIONS_URL = 'https://image.pollinations.ai/prompt/'
POLLINATIONS_MODEL = 'flux'

# ===================================
# Funciones auxiliares
# ===================================

def mejorar_prompt(prompt_usuario):
    return f"{prompt_usuario}, high quality, detailed, professional, 4k, masterpiece"

def formato_a_dimensiones(formato):
    formatos = {
        '1:1': (1024, 1024),
        '16:9': (1280, 720),
        '9:16': (720, 1280)
    }
    return formatos.get(formato, (1024, 1024))

# ===================================
# 🥇 NVIDIA FLUX.1-schnell (CREAR)
# ===================================

def generar_con_nvidia(prompt, width, height):
    if not NVIDIA_API_KEY:
        return None, "NVIDIA API Key no configurada"

    try:
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "seed": random.randint(1, 999999),
            "steps": 4
        }

        response = requests.post(
            NVIDIA_FLUX_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            if 'artifacts' in data and len(data['artifacts']) > 0:
                imagen_b64 = data['artifacts'][0].get('base64', '')
            elif 'image' in data:
                imagen_b64 = data['image']
            else:
                return None, f"NVIDIA: formato inesperado - {str(data)[:200]}"

            imagen_url = f"data:image/png;base64,{imagen_b64}"
            return imagen_url, None
        else:
            return None, f"NVIDIA Código {response.status_code}: {response.text[:200]}"

    except Exception as e:
        return None, f"NVIDIA Error: {str(e)}"

# ===================================
# 🎨 Pollinations Kontext (EDITAR)
# ===================================

def editar_con_pollinations(prompt, imagen_base64):
    """
    Edita imagen usando Pollinations AI Kontext (image-to-image).
    Gratis, sin API key.
    """
    try:
        # Limpiar prefijo si existe
        if ',' in imagen_base64:
            imagen_base64 = imagen_base64.split(',')[1]

        prompt_codificado = urllib.parse.quote(prompt)
        seed = random.randint(1, 999999)

        # Pollinations Kontext = modelo de edición
        imagen_url = (
            f"https://image.pollinations.ai/prompt/{prompt_codificado}"
            f"?model=kontext"
            f"&width=1024"
            f"&height=1024"
            f"&seed={seed}"
            f"&nologo=true"
            f"&image=data:image/png;base64,{imagen_base64}"
        )

        response = requests.get(imagen_url, timeout=120)

        if response.status_code == 200:
            imagen_editada_b64 = base64.b64encode(response.content).decode('utf-8')
            imagen_final = f"data:image/png;base64,{imagen_editada_b64}"
            return imagen_final, None
        else:
            return None, f"Pollinations Edit Código {response.status_code}: {response.text[:200]}"

    except Exception as e:
        return None, f"Pollinations Edit Error: {str(e)}"

# ===================================
# 🥈 Hugging Face (Respaldo Crear)
# ===================================

def generar_con_huggingface(prompt, width, height):
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
            imagen_bytes = response.content
            imagen_base64 = base64.b64encode(imagen_bytes).decode('utf-8')
            imagen_url = f"data:image/png;base64,{imagen_base64}"
            return imagen_url, None
        else:
            return None, f"HF Código {response.status_code}: {response.text[:200]}"

    except Exception as e:
        return None, f"HF Error: {str(e)}"

# ===================================
# 🥉 Pollinations AI (Último respaldo crear)
# ===================================

def generar_con_pollinations(prompt, width, height):
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
# Endpoint principal: CREAR
# ===================================

@imagen_bp.route('/crear', methods=['POST'])
def crear_imagen():
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

        formato = data.get('formato', '1:1')
        width, height = formato_a_dimensiones(formato)
        prompt_mejorado = mejorar_prompt(prompt_original)

        # 🥇 NVIDIA FLUX
        imagen_url, error_nv = generar_con_nvidia(prompt_mejorado, width, height)
        if imagen_url:
            return jsonify({
                'imagen_url': imagen_url,
                'prompt_usado': prompt_mejorado,
                'prompt_original': prompt_original,
                'proveedor': 'NVIDIA FLUX.1-schnell',
                'formato': formato,
                'success': True
            })

        print(f"⚠️ NVIDIA falló: {error_nv}")

        # 🥈 Hugging Face
        imagen_url, error_hf = generar_con_huggingface(prompt_mejorado, width, height)
        if imagen_url:
            return jsonify({
                'imagen_url': imagen_url,
                'prompt_usado': prompt_mejorado,
                'prompt_original': prompt_original,
                'proveedor': 'Hugging Face (respaldo)',
                'formato': formato,
                'success': True,
                'nota_nvidia': error_nv
            })

        print(f"⚠️ Hugging Face falló: {error_hf}")

        # 🥉 Pollinations
        imagen_url, error_pol = generar_con_pollinations(prompt_mejorado, width, height)
        if imagen_url:
            return jsonify({
                'imagen_url': imagen_url,
                'prompt_usado': prompt_mejorado,
                'prompt_original': prompt_original,
                'proveedor': 'Pollinations AI (respaldo final)',
                'formato': formato,
                'success': True,
                'nota_nvidia': error_nv,
                'nota_hf': error_hf
            })

        return jsonify({
            'error': 'Todos los proveedores fallaron',
            'message': f'NVIDIA: {error_nv} | HF: {error_hf} | Pollinations: {error_pol}',
            'success': False
        }), 500

    except Exception as e:
        return jsonify({
            'error': 'Error al crear imagen',
            'message': str(e),
            'success': False
        }), 500

# ===================================
# Endpoint: EDITAR imagen
# ===================================

@imagen_bp.route('/editar', methods=['POST'])
def editar_imagen():
    try:
        data = request.get_json()

        if not data or 'prompt' not in data or 'imagen_base64' not in data:
            return jsonify({
                'error': 'Faltan datos',
                'message': 'Debes enviar "prompt" e "imagen_base64"'
            }), 400

        prompt = data['prompt'].strip()
        imagen_base64 = data['imagen_base64']

        if not prompt:
            return jsonify({
                'error': 'Prompt vacío',
                'message': 'Describe cómo editar la imagen'
            }), 400

        imagen_url, error = editar_con_pollinations(prompt, imagen_base64)

        if imagen_url:
            return jsonify({
                'imagen_url': imagen_url,
                'prompt_usado': prompt,
                'proveedor': 'Pollinations Kontext (edición)',
                'success': True
            })

        return jsonify({
            'error': 'Error al editar imagen',
            'message': error,
            'success': False
        }), 500

    except Exception as e:
        return jsonify({
            'error': 'Error al editar imagen',
            'message': str(e),
            'success': False
        }), 500

# ===================================
# Endpoint de prueba
# ===================================

@imagen_bp.route('/test', methods=['GET'])
def test():
    return jsonify({
        'status': 'ok',
        'endpoint': 'imagen',
        'nvidia_configurado': bool(NVIDIA_API_KEY),
        'huggingface_configurado': bool(HUGGINGFACE_API_KEY),
        'pollinations_disponible': True,
        'modelo_crear': 'NVIDIA FLUX.1-schnell',
        'modelo_editar': 'Pollinations Kontext',
        'message': '🎨 Sistema imagen: NVIDIA + HF + Pollinations activo'
    })
