# ===================================
# imagen.py - Endpoint Crear/Editar Imagen
# ===================================
# 🥇 Crear: Cloudflare Workers AI (FLUX-1-schnell)
# 🎨 Editar: Cloudflare Workers AI (Stable Diffusion Img2Img)
# 🥈 Respaldo crear: Pollinations AI
# ===================================

import os
import base64
import random
import urllib.parse
import requests
from flask import Blueprint, request, jsonify

imagen_bp = Blueprint('imagen', __name__)

# ===================================
# Configuración
# ===================================

CLOUDFLARE_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID')
CLOUDFLARE_API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN')

# Cloudflare Workers AI - Crear (FLUX-1-schnell)
CLOUDFLARE_FLUX_URL = (
    f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}"
    f"/ai/run/@cf/black-forest-labs/flux-1-schnell"
) if CLOUDFLARE_ACCOUNT_ID else None

# Cloudflare Workers AI - Editar (Stable Diffusion Img2Img)
CLOUDFLARE_EDIT_URL = (
    f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}"
    f"/ai/run/@cf/runwayml/stable-diffusion-v1-5-img2img"
) if CLOUDFLARE_ACCOUNT_ID else None

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
# 🥇 Cloudflare Workers AI - FLUX schnell (CREAR)
# ===================================

def crear_con_cloudflare(prompt, width, height):
    """
    Genera imagen usando Cloudflare Workers AI (FLUX-1-schnell).
    Gratis: 10,000 requests/día.
    """
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        return None, "Cloudflare no configurado"

    try:
        headers = {
            "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": prompt,
            "steps": 4,
            "width": width,
            "height": height
        }

        response = requests.post(
            CLOUDFLARE_FLUX_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()

            if data.get('success') and 'result' in data:
                imagen_b64 = data['result'].get('image', '')
                if imagen_b64:
                    imagen_url = f"data:image/png;base64,{imagen_b64}"
                    return imagen_url, None
                else:
                    return None, f"Cloudflare: no devolvió imagen - {str(data)[:200]}"
            else:
                return None, f"Cloudflare respuesta inesperada: {str(data)[:200]}"
        else:
            return None, f"Cloudflare Código {response.status_code}: {response.text[:200]}"

    except Exception as e:
        return None, f"Cloudflare Error: {str(e)}"

# ===================================
# 🎨 Cloudflare Workers AI - Img2Img (EDITAR)
# ===================================

def editar_con_cloudflare(prompt, imagen_base64):
    """
    Edita imagen usando Cloudflare Stable Diffusion Img2Img.
    Recibe la imagen en base64 y la transforma con el prompt.
    """
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        return None, "Cloudflare no configurado"

    try:
        # Limpiar prefijo si existe
        if ',' in imagen_base64:
            imagen_base64 = imagen_base64.split(',')[1]

        # Decodificar base64 a bytes → luego a array de enteros (formato que Cloudflare acepta)
        imagen_bytes = base64.b64decode(imagen_base64)
        imagen_array = list(imagen_bytes)

        headers = {
            "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": prompt,
            "image": imagen_array,
            "strength": 0.7,  # Qué tanto modificar (0=nada, 1=totalmente nueva)
            "num_steps": 20,
            "guidance": 7.5
        }

        response = requests.post(
            CLOUDFLARE_EDIT_URL,
            headers=headers,
            json=payload,
            timeout=120
        )

        if response.status_code == 200:
            # Este endpoint devuelve la imagen directamente como bytes binarios
            content_type = response.headers.get('Content-Type', '')

            if 'image' in content_type:
                imagen_editada_b64 = base64.b64encode(response.content).decode('utf-8')
                imagen_final = f"data:image/png;base64,{imagen_editada_b64}"
                return imagen_final, None
            else:
                # Puede devolver JSON con la imagen en base64
                try:
                    data = response.json()
                    if data.get('success') and 'result' in data:
                        imagen_b64 = data['result'].get('image', '')
                        if imagen_b64:
                            return f"data:image/png;base64,{imagen_b64}", None
                    return None, f"Cloudflare Edit respuesta inesperada: {str(data)[:200]}"
                except:
                    # Si no es JSON, probablemente son bytes de imagen
                    imagen_editada_b64 = base64.b64encode(response.content).decode('utf-8')
                    imagen_final = f"data:image/png;base64,{imagen_editada_b64}"
                    return imagen_final, None
        else:
            return None, f"Cloudflare Edit Código {response.status_code}: {response.text[:200]}"

    except Exception as e:
        return None, f"Cloudflare Edit Error: {str(e)}"

# ===================================
# 🥈 Pollinations AI (Respaldo crear)
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

        # 🥇 Cloudflare Workers AI
        print("🦉 Creando imagen con Cloudflare Workers AI...")
        imagen_url, error_cf = crear_con_cloudflare(prompt_mejorado, width, height)
        if imagen_url:
            return jsonify({
                'imagen_url': imagen_url,
                'prompt_usado': prompt_mejorado,
                'prompt_original': prompt_original,
                'proveedor': 'Didasko AI',
                'formato': formato,
                'success': True
            })

        print(f"⚠️ Cloudflare falló: {error_cf}")

        # 🥈 Pollinations (respaldo)
        print("🔄 Intentando con respaldo Pollinations...")
        imagen_url, error_pol = generar_con_pollinations(prompt_mejorado, width, height)
        if imagen_url:
            return jsonify({
                'imagen_url': imagen_url,
                'prompt_usado': prompt_mejorado,
                'prompt_original': prompt_original,
                'proveedor': 'Didasko AI Respaldo',
                'formato': formato,
                'success': True,
                'nota_cloudflare': error_cf
            })

        return jsonify({
            'error': 'Todos los proveedores fallaron',
            'message': f'Cloudflare: {error_cf} | Pollinations: {error_pol}',
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

        print("🎨 Editando imagen con Cloudflare Img2Img...")
        imagen_url, error = editar_con_cloudflare(prompt, imagen_base64)

        if imagen_url:
            return jsonify({
                'imagen_url': imagen_url,
                'prompt_usado': prompt,
                'proveedor': 'Didasko AI',
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
        'cloudflare_configurado': bool(CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN),
        'pollinations_disponible': True,
        'modelo_crear': 'Cloudflare FLUX-1-schnell',
        'modelo_editar': 'Cloudflare Stable Diffusion Img2Img',
        'message': '🎨 Sistema imagen Cloudflare completo'
    })
