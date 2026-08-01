# ===================================
# imagen.py - Endpoint Crear/Editar Imagen
# ===================================
# 🥇 Crear + Editar: Google Gemini 2.0 Flash Image
# 🥈 Respaldo crear: Pollinations AI
# ===================================

import os
import base64
import random
import urllib.parse
from io import BytesIO
from flask import Blueprint, request, jsonify
from google import genai
from google.genai import types
from PIL import Image
import requests

imagen_bp = Blueprint('imagen', __name__)

# ===================================
# Configuración
# ===================================

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

POLLINATIONS_URL = 'https://image.pollinations.ai/prompt/'
POLLINATIONS_MODEL = 'flux'

# Modelo Gemini para imágenes
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image-preview"

# Cliente Gemini
gemini_client = None
if GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"⚠️ Error inicializando Gemini: {e}")

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
# 🥇 Google Gemini (CREAR imagen)
# ===================================

def crear_con_gemini(prompt):
    """
    Genera imagen usando Google Gemini 2.0 Flash Image Generation.
    """
    if not gemini_client:
        return None, "Gemini API Key no configurada"

    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_IMAGE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=['Text', 'Image']
            )
        )

        # Buscar la imagen en la respuesta
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                imagen_bytes = part.inline_data.data
                imagen_b64 = base64.b64encode(imagen_bytes).decode('utf-8')
                imagen_url = f"data:image/png;base64,{imagen_b64}"
                return imagen_url, None

        return None, "Gemini no devolvió imagen"

    except Exception as e:
        return None, f"Gemini Error: {str(e)}"

# ===================================
# 🎨 Google Gemini (EDITAR imagen)
# ===================================

def editar_con_gemini(prompt, imagen_base64):
    """
    Edita imagen usando Google Gemini 2.0 Flash Image Generation.
    """
    if not gemini_client:
        return None, "Gemini API Key no configurada"

    try:
        # Limpiar prefijo si existe
        if ',' in imagen_base64:
            imagen_base64 = imagen_base64.split(',')[1]

        # Convertir base64 a PIL Image
        imagen_bytes = base64.b64decode(imagen_base64)
        imagen_pil = Image.open(BytesIO(imagen_bytes))

        # Convertir a RGB si es necesario
        if imagen_pil.mode != 'RGB':
            imagen_pil = imagen_pil.convert('RGB')

        # Enviar imagen + prompt a Gemini
        response = gemini_client.models.generate_content(
            model=GEMINI_IMAGE_MODEL,
            contents=[prompt, imagen_pil],
            config=types.GenerateContentConfig(
                response_modalities=['Text', 'Image']
            )
        )

        # Buscar la imagen editada en la respuesta
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                imagen_editada_bytes = part.inline_data.data
                imagen_b64 = base64.b64encode(imagen_editada_bytes).decode('utf-8')
                imagen_url = f"data:image/png;base64,{imagen_b64}"
                return imagen_url, None

        return None, "Gemini no devolvió imagen editada"

    except Exception as e:
        return None, f"Gemini Edit Error: {str(e)}"

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

        # 🥇 Google Gemini
        print("🦉 Creando imagen con Gemini...")
        imagen_url, error_gemini = crear_con_gemini(prompt_mejorado)
        if imagen_url:
            return jsonify({
                'imagen_url': imagen_url,
                'prompt_usado': prompt_mejorado,
                'prompt_original': prompt_original,
                'proveedor': 'Didasko AI',
                'formato': formato,
                'success': True
            })

        print(f"⚠️ Gemini falló: {error_gemini}")

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
                'nota_gemini': error_gemini
            })

        return jsonify({
            'error': 'Todos los proveedores fallaron',
            'message': f'Gemini: {error_gemini} | Pollinations: {error_pol}',
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

        print("🎨 Editando imagen con Gemini...")
        imagen_url, error = editar_con_gemini(prompt, imagen_base64)

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
        'gemini_configurado': bool(GEMINI_API_KEY),
        'pollinations_disponible': True,
        'modelo_crear': 'Google Gemini 2.0 Flash Image',
        'modelo_editar': 'Google Gemini 2.0 Flash Image',
        'message': '🎨 Sistema imagen con Gemini activo'
    })
