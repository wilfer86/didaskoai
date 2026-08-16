# ===================================
# imagen.py - Endpoint Crear/Editar Imagen V4.1
# ===================================
# 🥇 Crear: Gemini 2.0 Flash Image (Nano Banana)
# 🥈 Respaldo: Cloudflare Workers AI
# 🥉 Último respaldo: Pollinations AI
# 🔒 Proveedor oculto: siempre "Didasko AI"
# ===================================

import os
import base64
import random
import urllib.parse
import requests
from io import BytesIO
from flask import Blueprint, request, jsonify, session
from PIL import Image
from supabase_client import get_client, subir_imagen_storage

imagen_bp = Blueprint('imagen', __name__)

# ===================================
# Configuración
# ===================================

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# 🆕 Modelo correcto de Gemini para imágenes
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_IMAGE_MODEL}:generateContent"

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

# 🔒 Nombre público del proveedor (oculta el modelo real)
PROVEEDOR_PUBLICO = "Didasko AI"

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

def redimensionar_imagen(imagen_bytes, ancho_destino, alto_destino):
    try:
        imagen = Image.open(BytesIO(imagen_bytes))
        if imagen.mode != 'RGB':
            imagen = imagen.convert('RGB')
        imagen_redimensionada = imagen.resize((ancho_destino, alto_destino), Image.LANCZOS)
        buffer = BytesIO()
        imagen_redimensionada.save(buffer, format='PNG', quality=95)
        return buffer.getvalue()
    except Exception as e:
        print(f"⚠️ Error redimensionando: {e}")
        return imagen_bytes

def obtener_bytes_imagen(imagen_input):
    """Convierte cualquier formato a bytes."""
    try:
        if imagen_input.startswith('http'):
            print(f"📥 Descargando imagen desde URL...")
            response = requests.get(imagen_input, timeout=30)
            if response.status_code != 200:
                return None, f"No se pudo descargar imagen: {response.status_code}"
            return response.content, None
        
        if imagen_input.startswith('data:image'):
            imagen_input = imagen_input.split(',')[1]
        
        missing_padding = len(imagen_input) % 4
        if missing_padding:
            imagen_input += '=' * (4 - missing_padding)
        
        imagen_bytes = base64.b64decode(imagen_input)
        return imagen_bytes, None
        
    except Exception as e:
        return None, f"Error decodificando imagen: {str(e)}"

def guardar_imagen_db(usuario_id, url_publica, prompt, formato, tipo):
    """Guarda registro en tabla imagenes."""
    try:
        client = get_client()
        if not client:
            return
        
        client.table('imagenes').insert({
            'usuario_id': usuario_id,
            'url': url_publica,
            'prompt': prompt[:500],
            'formato': formato,
            'tipo': tipo
        }).execute()
        print(f"✅ Registro guardado en DB")
    except Exception as e:
        print(f"⚠️ No se guardó registro: {e}")

# ===================================
# 🥇 GEMINI FLASH IMAGE (Nano Banana)
# ===================================

def crear_con_gemini(prompt):
    """Crea imagen con Gemini 2.0 Flash Image Generation."""
    if not GEMINI_API_KEY:
        return None, "Gemini no configurado"

    try:
        url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"]
            }
        }
        
        headers = {"Content-Type": "application/json"}
        
        print("🎨 Generando con motor premium...")
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        
        if response.status_code == 200:
            data = response.json()
            candidates = data.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                for part in parts:
                    if 'inlineData' in part:
                        imagen_b64 = part['inlineData'].get('data', '')
                        mime_type = part['inlineData'].get('mimeType', 'image/png')
                        if imagen_b64:
                            print("✅ Imagen premium generada")
                            return f"data:{mime_type};base64,{imagen_b64}", None
            
            return None, "Sin imagen en respuesta"
        
        error_msg = response.text[:300]
        print(f"⚠️ Motor premium status {response.status_code}")
        return None, f"Código {response.status_code}: {error_msg}"
        
    except Exception as e:
        return None, f"Error: {str(e)}"


def editar_con_gemini(prompt, imagen_input):
    """Edita imagen con Gemini."""
    if not GEMINI_API_KEY:
        return None, "Gemini no configurado"

    try:
        imagen_bytes, error = obtener_bytes_imagen(imagen_input)
        if error:
            return None, error
        
        imagen_b64 = base64.b64encode(imagen_bytes).decode('utf-8')
        
        try:
            img = Image.open(BytesIO(imagen_bytes))
            mime_type = f"image/{img.format.lower()}" if img.format else "image/png"
        except:
            mime_type = "image/png"
        
        url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": imagen_b64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"]
            }
        }
        
        headers = {"Content-Type": "application/json"}
        
        print("🎨 Editando con motor premium...")
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            candidates = data.get('candidates', [])
            if candidates:
                parts = candidates[0].get('content', {}).get('parts', [])
                for part in parts:
                    if 'inlineData' in part:
                        imagen_b64_edit = part['inlineData'].get('data', '')
                        mime_out = part['inlineData'].get('mimeType', 'image/png')
                        if imagen_b64_edit:
                            print("✅ Imagen editada premium")
                            return f"data:{mime_out};base64,{imagen_b64_edit}", None
            
            return None, "Sin imagen en respuesta"
        
        error_msg = response.text[:300]
        return None, f"Código {response.status_code}: {error_msg}"
        
    except Exception as e:
        return None, f"Error: {str(e)}"

# ===================================
# 🥈 Cloudflare Workers AI - CREAR
# ===================================

def crear_con_cloudflare(prompt, width, height):
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
        response = requests.post(CLOUDFLARE_FLUX_URL, headers=headers, json=payload, timeout=60)

        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'result' in data:
                imagen_b64 = data['result'].get('image', '')
                if imagen_b64:
                    return f"data:image/png;base64,{imagen_b64}", None
                return None, "Cloudflare: sin imagen"
            return None, "Cloudflare respuesta inesperada"
        return None, f"Cloudflare Código {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, f"Cloudflare Error: {str(e)}"

# ===================================
# 🥈 Cloudflare Img2Img - EDITAR
# ===================================

def editar_con_cloudflare(prompt, imagen_input):
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        return None, "Cloudflare no configurado"

    try:
        imagen_bytes, error = obtener_bytes_imagen(imagen_input)
        if error:
            return None, error
        
        try:
            imagen_pil = Image.open(BytesIO(imagen_bytes))
            ancho_original, alto_original = imagen_pil.size
        except:
            ancho_original, alto_original = 1024, 1024

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
        response = requests.post(CLOUDFLARE_EDIT_URL, headers=headers, json=payload, timeout=120)

        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
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
                return None, "Cloudflare Edit: sin imagen"

            imagen_final_bytes = redimensionar_imagen(imagen_editada_bytes, ancho_original, alto_original)
            imagen_final_b64 = base64.b64encode(imagen_final_bytes).decode('utf-8')
            return f"data:image/png;base64,{imagen_final_b64}", None
        return None, f"Cloudflare Edit Código {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, f"Cloudflare Edit Error: {str(e)}"

# ===================================
# 🥉 Pollinations AI
# ===================================

def generar_con_pollinations(prompt, width, height):
    try:
        prompt_codificado = urllib.parse.quote(prompt)
        seed = random.randint(1, 999999)
        imagen_url = (
            f"{POLLINATIONS_URL}{prompt_codificado}"
            f"?model={POLLINATIONS_MODEL}"
            f"&width={width}&height={height}&seed={seed}"
            f"&nologo=true&enhance=true"
        )
        return imagen_url, None
    except Exception as e:
        return None, f"Pollinations Error: {str(e)}"

# ===================================
# Endpoint: CREAR
# ===================================

@imagen_bp.route('/crear', methods=['POST'])
def crear_imagen():
    try:
        data = request.get_json()

        if not data or 'prompt' not in data:
            return jsonify({'error': 'Falta el prompt'}), 400

        prompt_original = data['prompt'].strip()
        if not prompt_original:
            return jsonify({'error': 'Prompt vacío'}), 400

        formato = data.get('formato', '1:1')
        width, height = formato_a_dimensiones(formato)
        prompt_mejorado = mejorar_prompt(prompt_original)

        usuario_id = session.get('usuario_id')

        # 🥇 GEMINI (Premium)
        imagen_url, error_gemini = crear_con_gemini(prompt_mejorado)
        
        # 🥈 CLOUDFLARE (Respaldo)
        if not imagen_url:
            print(f"⚠️ Motor premium falló: {error_gemini}")
            print("🔄 Usando motor secundario...")
            imagen_url, error_cf = crear_con_cloudflare(prompt_mejorado, width, height)
            
            if not imagen_url and error_cf and "400" in str(error_cf):
                print("🔄 Reintentando...")
                imagen_url, error_cf = crear_con_cloudflare(prompt_mejorado, width, height)
        
        # 🥉 POLLINATIONS (Último respaldo)
        if not imagen_url:
            print("🔄 Usando motor de respaldo...")
            imagen_url, error_pol = generar_con_pollinations(prompt_mejorado, width, height)
            
            if not imagen_url:
                return jsonify({
                    'error': 'Servicio temporalmente no disponible',
                    'message': 'Todos los motores fallaron. Intenta en 1 minuto.',
                    'success': False
                }), 500
        
        # Guardar en Storage
        url_publica = imagen_url
        if usuario_id:
            print("📤 Guardando en tu galería...")
            url_publica = subir_imagen_storage(imagen_url, usuario_id, 'creada')
            guardar_imagen_db(usuario_id, url_publica, prompt_original, formato, 'creada')

        return jsonify({
            'imagen_url': url_publica,
            'prompt_usado': prompt_mejorado,
            'prompt_original': prompt_original,
            'proveedor': PROVEEDOR_PUBLICO,
            'formato': formato,
            'success': True
        })

    except Exception as e:
        return jsonify({'error': 'Error al crear imagen', 'message': str(e), 'success': False}), 500

# ===================================
# Endpoint: EDITAR
# ===================================

@imagen_bp.route('/editar', methods=['POST'])
def editar_imagen():
    try:
        data = request.get_json()
        if not data or 'prompt' not in data or 'imagen_base64' not in data:
            return jsonify({'error': 'Faltan datos'}), 400

        prompt = data['prompt'].strip()
        imagen_input = data['imagen_base64']

        if not prompt:
            return jsonify({'error': 'Prompt vacío'}), 400

        if not imagen_input:
            return jsonify({'error': 'Falta imagen'}), 400

        usuario_id = session.get('usuario_id')

        # 🥇 GEMINI (Premium)
        imagen_url, error_gemini = editar_con_gemini(prompt, imagen_input)

        # 🥈 CLOUDFLARE (Respaldo)
        if not imagen_url:
            print(f"⚠️ Motor premium falló: {error_gemini}")
            print("🔄 Usando motor secundario...")
            imagen_url, error_cf = editar_con_cloudflare(prompt, imagen_input)

            if not imagen_url and error_cf and "400" in str(error_cf):
                print("🔄 Reintentando...")
                imagen_url, error_cf = editar_con_cloudflare(prompt, imagen_input)

            if not imagen_url:
                return jsonify({
                    'error': 'No se pudo editar la imagen',
                    'message': 'Intenta con otra descripción o imagen',
                    'success': False
                }), 500

        # Guardar en Storage
        url_publica = imagen_url
        if usuario_id:
            print("📤 Guardando imagen editada...")
            url_publica = subir_imagen_storage(imagen_url, usuario_id, 'editada')
            guardar_imagen_db(usuario_id, url_publica, prompt, 'editada', 'editada')

        return jsonify({
            'imagen_url': url_publica,
            'prompt_usado': prompt,
            'proveedor': PROVEEDOR_PUBLICO,
            'success': True
        })

    except Exception as e:
        return jsonify({'error': 'Error', 'message': str(e), 'success': False}), 500

# ===================================
# Endpoint: HISTORIAL
# ===================================

@imagen_bp.route('/historial', methods=['GET'])
def obtener_historial_imagenes():
    try:
        usuario_id = session.get('usuario_id')
        if not usuario_id:
            return jsonify({'success': False, 'error': 'Sin sesión'}), 401

        client = get_client()
        limite = int(request.args.get('limite', 20))

        resultado = client.table('imagenes').select('*').eq('usuario_id', usuario_id).order('fecha', desc=True).limit(limite).execute()

        return jsonify({
            'success': True,
            'total': len(resultado.data),
            'imagenes': resultado.data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===================================
# Endpoint: ELIMINAR
# ===================================

@imagen_bp.route('/eliminar/<imagen_id>', methods=['DELETE'])
def eliminar_imagen_historial(imagen_id):
    try:
        usuario_id = session.get('usuario_id')
        if not usuario_id:
            return jsonify({'success': False, 'error': 'Sin sesión'}), 401

        client = get_client()
        client.table('imagenes').delete().eq('id', imagen_id).eq('usuario_id', usuario_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===================================
# Endpoint de prueba
# ===================================

@imagen_bp.route('/test', methods=['GET'])
def test():
    return jsonify({
        'status': 'ok',
        'endpoint': 'imagen',
        'version': 'V4.1 - Didasko AI Motor Premium',
        'motor_premium_configurado': bool(GEMINI_API_KEY),
        'motor_secundario_configurado': bool(CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN),
        'usuario_logueado': session.get('usuario_id') is not None,
        'creado_por': 'Didasko AI'
    })
