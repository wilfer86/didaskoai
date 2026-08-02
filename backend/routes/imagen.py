# ===================================
# imagen.py - Endpoint Crear/Editar Imagen
# ===================================
# 🥇 Crear: Cloudflare Workers AI (FLUX-1-schnell)
# 🎨 Editar: Cloudflare Workers AI (SD 1.5 Img2Img) + Pillow (respetar formato)
# 🥈 Respaldo crear: Pollinations AI
# ===================================

import os
import base64
import random
import urllib.parse
import requests
from io import BytesIO
from flask import Blueprint, request, jsonify
from PIL import Image

imagen_bp = Blueprint('imagen', __name__)

# ===================================
# Configuración
# ===================================

CLOUDFLARE_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID')
CLOUDFLARE_API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN')

CLOUDFLARE_FLUX_URL = (
    f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}"
    f"/ai/run/@cf/black-forest-labs/flux-1-schnell"
) if CLOUDFLARE_ACCOUNT_ID else None

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

def obtener_dimensiones_imagen(imagen_base64):
    """
    Obtiene el ancho y alto de una imagen en base64.
    """
    try:
        if ',' in imagen_base64:
            imagen_base64 = imagen_base64.split(',')[1]
        imagen_bytes = base64.b64decode(imagen_base64)
        imagen = Image.open(BytesIO(imagen_bytes))
        return imagen.size  # (width, height)
    except:
        return (1024, 1024)

def redimensionar_imagen(imagen_bytes, ancho_destino, alto_destino):
    """
    Redimensiona una imagen a las dimensiones deseadas manteniendo calidad.
    """
    try:
        imagen = Image.open(BytesIO(imagen_bytes))
        # Convertir a RGB si es necesario
        if imagen.mode != 'RGB':
            imagen = imagen.convert('RGB')
        # Redimensionar con alta calidad
        imagen_redimensionada = imagen.resize((ancho_destino, alto_destino), Image.LANCZOS)
        # Convertir de vuelta a bytes
        buffer = BytesIO()
        imagen_redimensionada.save(buffer, format='PNG', quality=95)
        return buffer.getvalue()
    except Exception as e:
        print(f"⚠️ Error redimensionando: {e}")
        return imagen_bytes

# ===================================
# 🥇 Cloudflare Workers AI - FLUX schnell (CREAR)
# ===================================

def crear_con_cloudflare(prompt, width, height):
    """
    Genera imagen usando Cloudflare Workers AI (FLUX-1-schnell).
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
# 🎨 Cloudflare Workers AI - Img2Img (EDITAR) + Pillow redimensionar
# ===================================

def editar_con_cloudflare(prompt, imagen_base64):
    """
    Edita imagen con Cloudflare SD 1.5 Img2Img.
    Después redimensiona con Pillow para respetar el aspecto ratio original.
    """
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        return None, "Cloudflare no configurado"

    try:
        # Obtener dimensiones originales de la imagen
        ancho_original, alto_original = obtener_dimensiones_imagen(imagen_base64)
        print(f"📐 Imagen original: {ancho_original}x{alto_original}")

        # Limpiar prefijo si existe
        if ',' in imagen_base64:
            imagen_base64 = imagen_base64.split(',')[1]

        # Decodificar base64 → bytes → lista de enteros (formato Cloudflare)
        imagen_bytes = base64.b64decode(imagen_base64)
        imagen_array = list(imagen_bytes)

        headers = {
            "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": prompt,
            "image": imagen_array,
            "strength": 0.7,
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
            content_type = response.headers.get('Content-Type', '')

            # Obtener los bytes de la imagen editada
            imagen_editada_bytes = None

            if 'image' in content_type:
                imagen_editada_bytes = response.content
            else:
                try:
                    data = response.json()
                    if data.get('success') and 'result' in data:
                        imagen_b64_edit = data['result'].get('image', '')
                        if imagen_b64_edit:
                            imagen_editada_bytes = base64.b64decode(imagen_b64_edit)
                except:
                    imagen_editada_bytes = response.content

            if not imagen_editada_bytes:
                return None, "Cloudflare Edit: no devolvió imagen"

            # 🎨 Redimensionar al tamaño original de la imagen que subió el usuario
            print(f"🔧 Redimensionando a {ancho_original}x{alto_original}...")
            imagen_final_bytes = redimensionar_imagen(imagen_editada_bytes, ancho_original, alto_original)

            # Convertir a base64 para devolver
            imagen_final_b64 = base64.b64encode(imagen_final_bytes).decode('utf-8')
            imagen_final = f"data:image/png;base64,{imagen_final_b64}"
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
        'modelo_editar': 'Cloudflare SD 1.5 Img2Img + Pillow resize',
        'message': '🎨 Sistema imagen completo'
    })
