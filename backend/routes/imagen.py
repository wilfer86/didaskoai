# ===================================
# imagen.py - Endpoint Crear/Editar Imagen V3.2
# ===================================
# 🥇 Crear: Cloudflare Workers AI (FLUX-1-schnell)
# 🎨 Editar: Cloudflare Workers AI (SD 1.5 Img2Img) + Pillow
# 🥈 Respaldo crear: Pollinations AI
# 🆕 Sube imágenes a Supabase Storage
# 🆕 Editar acepta URLs de Storage (no solo base64)
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
    try:
        if ',' in imagen_base64:
            imagen_base64 = imagen_base64.split(',')[1]
        # Arreglar padding
        missing_padding = len(imagen_base64) % 4
        if missing_padding:
            imagen_base64 += '=' * (4 - missing_padding)
        imagen_bytes = base64.b64decode(imagen_base64)
        imagen = Image.open(BytesIO(imagen_bytes))
        return imagen.size
    except:
        return (1024, 1024)

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

# ===================================
# 🆕 Función universal: obtener bytes de imagen
# Acepta: base64, data:image, URL http/https
# ===================================
def obtener_bytes_imagen(imagen_input):
    """
    Convierte cualquier formato de entrada a bytes de imagen.
    Devuelve: (imagen_bytes, error)
    """
    try:
        # Caso 1: URL (http o https) - descargar
        if imagen_input.startswith('http'):
            print(f"📥 Descargando imagen desde URL...")
            response = requests.get(imagen_input, timeout=30)
            if response.status_code != 200:
                return None, f"No se pudo descargar imagen: {response.status_code}"
            return response.content, None
        
        # Caso 2: base64 con prefijo data:image
        if imagen_input.startswith('data:image'):
            imagen_input = imagen_input.split(',')[1]
        
        # Caso 3: base64 puro
        # Arreglar padding
        missing_padding = len(imagen_input) % 4
        if missing_padding:
            imagen_input += '=' * (4 - missing_padding)
        
        imagen_bytes = base64.b64decode(imagen_input)
        return imagen_bytes, None
        
    except Exception as e:
        return None, f"Error decodificando imagen: {str(e)}"

# ===================================
# 🆕 Guardar registro en Supabase (URL corta)
# ===================================
def guardar_imagen_db(usuario_id, url_publica, prompt, formato, tipo):
    """Guarda solo el registro (URL corta) en la tabla imagenes."""
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
        print(f"✅ Registro de imagen guardado en DB")
    except Exception as e:
        print(f"⚠️ No se guardó registro: {e}")

# ===================================
# 🥇 Cloudflare Workers AI - FLUX schnell (CREAR)
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
                return None, f"Cloudflare: sin imagen"
            return None, f"Cloudflare respuesta inesperada"
        return None, f"Cloudflare Código {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, f"Cloudflare Error: {str(e)}"

# ===================================
# 🎨 Cloudflare Workers AI - Img2Img (EDITAR)
# ===================================

def editar_con_cloudflare(prompt, imagen_input):
    """
    Edita imagen. Acepta base64, data:image o URL http/https.
    """
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        return None, "Cloudflare no configurado"

    try:
        # 🆕 Obtener bytes de imagen (funciona con URL o base64)
        imagen_bytes, error = obtener_bytes_imagen(imagen_input)
        if error:
            return None, error
        
        # Obtener dimensiones originales
        try:
            imagen_pil = Image.open(BytesIO(imagen_bytes))
            ancho_original, alto_original = imagen_pil.size
        except:
            ancho_original, alto_original = 1024, 1024
        
        print(f"📐 Imagen original: {ancho_original}x{alto_original}")

        # Convertir bytes a lista de enteros (formato Cloudflare)
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

            print(f"🔧 Redimensionando a {ancho_original}x{alto_original}...")
            imagen_final_bytes = redimensionar_imagen(imagen_editada_bytes, ancho_original, alto_original)
            imagen_final_b64 = base64.b64encode(imagen_final_bytes).decode('utf-8')
            return f"data:image/png;base64,{imagen_final_b64}", None
        return None, f"Cloudflare Edit Código {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, f"Cloudflare Edit Error: {str(e)}"

# ===================================
# 🥈 Pollinations AI (Respaldo)
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

        # 🥇 Cloudflare (con 1 reintento si falla la primera vez)
        print("🦉 Creando imagen con Cloudflare...")
        imagen_url, error_cf = crear_con_cloudflare(prompt_mejorado, width, height)
        
        # 🆕 Reintentar 1 vez si Cloudflare falla temporalmente
        if not imagen_url and error_cf and "400" in str(error_cf):
            print("🔄 Reintentando Cloudflare...")
            imagen_url, error_cf = crear_con_cloudflare(prompt_mejorado, width, height)
        
        if imagen_url:
            # 🆕 Subir a Supabase Storage y obtener URL pública
            url_publica = imagen_url
            if usuario_id:
                print("📤 Subiendo imagen a Storage...")
                url_publica = subir_imagen_storage(imagen_url, usuario_id, 'creada')
                guardar_imagen_db(usuario_id, url_publica, prompt_original, formato, 'creada')

            return jsonify({
                'imagen_url': url_publica,
                'prompt_usado': prompt_mejorado,
                'prompt_original': prompt_original,
                'proveedor': 'Didasko AI',
                'formato': formato,
                'success': True
            })

        print(f"⚠️ Cloudflare falló: {error_cf}")

        # 🥈 Pollinations
        print("🔄 Usando respaldo Pollinations...")
        imagen_url, error_pol = generar_con_pollinations(prompt_mejorado, width, height)
        if imagen_url:
            url_publica = imagen_url
            if usuario_id:
                print("📤 Subiendo imagen a Storage...")
                url_publica = subir_imagen_storage(imagen_url, usuario_id, 'creada')
                guardar_imagen_db(usuario_id, url_publica, prompt_original, formato, 'creada')

            return jsonify({
                'imagen_url': url_publica,
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
        imagen_input = data['imagen_base64']  # Puede ser base64 o URL

        if not prompt:
            return jsonify({'error': 'Prompt vacío'}), 400

        if not imagen_input:
            return jsonify({'error': 'Falta imagen'}), 400

        usuario_id = session.get('usuario_id')

        print("🎨 Editando imagen con Cloudflare Img2Img...")
        imagen_url, error = editar_con_cloudflare(prompt, imagen_input)

        # 🆕 Reintentar 1 vez si falla
        if not imagen_url and error and "400" in str(error):
            print("🔄 Reintentando Cloudflare Edit...")
            imagen_url, error = editar_con_cloudflare(prompt, imagen_input)

        if imagen_url:
            # 🆕 Subir a Storage
            url_publica = imagen_url
            if usuario_id:
                print("📤 Subiendo imagen editada a Storage...")
                url_publica = subir_imagen_storage(imagen_url, usuario_id, 'editada')
                guardar_imagen_db(usuario_id, url_publica, prompt, 'editada', 'editada')

            return jsonify({
                'imagen_url': url_publica,
                'prompt_usado': prompt,
                'proveedor': 'Didasko AI',
                'success': True
            })

        return jsonify({'error': 'Error al editar', 'message': error, 'success': False}), 500

    except Exception as e:
        return jsonify({'error': 'Error', 'message': str(e), 'success': False}), 500

# ===================================
# 🆕 Endpoint: HISTORIAL DE IMÁGENES
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
# 🆕 Endpoint: ELIMINAR imagen
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
        'cloudflare_configurado': bool(CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN),
        'usuario_logueado': session.get('usuario_id') is not None,
        'message': '🎨 Sistema imagen V3.2 con Storage y edición desde URL'
    })
