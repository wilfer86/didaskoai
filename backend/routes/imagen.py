# ===================================
# imagen.py - Endpoint Crear/Editar Imagen V6.1
# ===================================
# 🥇 Crear todos: Fal.ai FLUX.1-schnell ($0.003 c/u)
# 💎 Crear VIP: Fal.ai FLUX.1-dev ($0.025 c/u)
# 🎨 Editar todos: Fal.ai FLUX image-to-image ($0.025 c/u)
# 🔄 Respaldo: Cloudflare Workers AI (GRATIS)
# 🥉 Último respaldo: Pollinations
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

# 🆕 Fal.ai (Principal)
FAL_API_KEY = os.getenv('FAL_API_KEY')

# URLs de modelos Fal.ai
FAL_FLUX_SCHNELL_URL = "https://fal.run/fal-ai/flux/schnell"
FAL_FLUX_DEV_URL = "https://fal.run/fal-ai/flux/dev"
FAL_FLUX_EDIT_URL = "https://fal.run/fal-ai/flux/dev/image-to-image"

# Cloudflare (Respaldo)
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

# 🔒 Nombre público del proveedor
PROVEEDOR_PUBLICO = "Didasko AI"
PROVEEDOR_PREMIUM = "Didasko AI Premium"

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

def formato_a_fal(formato):
    """Fal.ai usa nombres específicos de tamaños."""
    formatos = {
        '1:1': 'square_hd',
        '16:9': 'landscape_16_9',
        '9:16': 'portrait_16_9'
    }
    return formatos.get(formato, 'square_hd')

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
                return None, f"No se pudo descargar: {response.status_code}"
            return response.content, None
        
        if imagen_input.startswith('data:image'):
            imagen_input = imagen_input.split(',')[1]
        
        missing_padding = len(imagen_input) % 4
        if missing_padding:
            imagen_input += '=' * (4 - missing_padding)
        
        imagen_bytes = base64.b64decode(imagen_input)
        return imagen_bytes, None
        
    except Exception as e:
        return None, f"Error: {str(e)}"

def guardar_imagen_db(usuario_id, url_publica, prompt, formato, tipo):
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

def verificar_es_vip(usuario_id):
    """Verifica si el usuario es VIP."""
    try:
        client = get_client()
        if not client or not usuario_id:
            return False
        
        result = client.table('usuarios').select('es_vip, vip_hasta').eq('id', usuario_id).execute()
        
        if result.data and len(result.data) > 0:
            user = result.data[0]
            if user.get('es_vip'):
                from datetime import datetime
                if user.get('vip_hasta'):
                    vip_hasta = datetime.fromisoformat(user['vip_hasta'].replace('Z', '+00:00'))
                    if vip_hasta > datetime.now(vip_hasta.tzinfo):
                        return True
        return False
    except Exception as e:
        print(f"⚠️ Error verificando VIP: {e}")
        return False

# ===================================
# 🥇 FAL.AI - CREAR
# ===================================

def crear_con_fal(prompt, formato, es_vip=False):
    """Crea imagen con Fal.ai."""
    if not FAL_API_KEY:
        return None, "Fal.ai no configurado"

    try:
        # Elegir modelo según VIP
        url_modelo = FAL_FLUX_DEV_URL if es_vip else FAL_FLUX_SCHNELL_URL
        tamano = formato_a_fal(formato)
        
        headers = {
            "Authorization": f"Key {FAL_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": prompt,
            "image_size": tamano,
            "num_inference_steps": 4 if not es_vip else 28,
            "num_images": 1,
            "enable_safety_checker": True
        }
        
        # FLUX.1-dev necesita guidance_scale
        if es_vip:
            payload["guidance_scale"] = 3.5
        
        print(f"🎨 Generando con motor {'premium' if es_vip else 'estándar'}...")
        response = requests.post(url_modelo, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            images = data.get('images', [])
            if images:
                imagen_url = images[0].get('url', '')
                if imagen_url:
                    print("✅ Imagen generada exitosamente")
                    return imagen_url, None
            
            return None, "Sin imagen en respuesta"
        
        error_msg = response.text[:300]
        print(f"⚠️ Fal.ai status {response.status_code}: {error_msg}")
        return None, f"Código {response.status_code}: {error_msg}"
        
    except Exception as e:
        return None, f"Error: {str(e)}"


def editar_con_fal(prompt, imagen_input):
    """Edita imagen con Fal.ai FLUX image-to-image."""
    if not FAL_API_KEY:
        return None, "Fal.ai no configurado"

    try:
        # Obtener bytes de imagen
        imagen_bytes, error = obtener_bytes_imagen(imagen_input)
        if error:
            return None, error
        
        # Convertir a base64 con prefijo data URI
        imagen_b64 = base64.b64encode(imagen_bytes).decode('utf-8')
        imagen_data_uri = f"data:image/png;base64,{imagen_b64}"
        
        headers = {
            "Authorization": f"Key {FAL_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # FLUX image-to-image para transformaciones
        payload = {
            "prompt": prompt,
            "image_url": imagen_data_uri,
            "strength": 0.85,
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
            "num_images": 1,
            "enable_safety_checker": True
        }
        
        print("🎨 Editando con motor premium...")
        response = requests.post(FAL_FLUX_EDIT_URL, headers=headers, json=payload, timeout=180)
        
        if response.status_code == 200:
            data = response.json()
            images = data.get('images', [])
            if images:
                imagen_url = images[0].get('url', '')
                if imagen_url:
                    print("✅ Imagen editada exitosamente")
                    return imagen_url, None
            
            return None, "Sin imagen en respuesta"
        
        error_msg = response.text[:300]
        print(f"⚠️ Fal.ai Edit status {response.status_code}: {error_msg}")
        return None, f"Código {response.status_code}: {error_msg}"
        
    except Exception as e:
        return None, f"Error: {str(e)}"

# ===================================
# 🔄 Cloudflare (Respaldo)
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
# 🥉 Pollinations (Último respaldo)
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
        
        # Verificar si es VIP para usar modelo premium
        es_vip = verificar_es_vip(usuario_id) if usuario_id else False
        proveedor_publico = PROVEEDOR_PREMIUM if es_vip else PROVEEDOR_PUBLICO

        # 🥇 FAL.AI (Principal)
        imagen_url, error_fal = crear_con_fal(prompt_mejorado, formato, es_vip)
        
        # Si el modelo VIP falla, intentar con el FREE
        if not imagen_url and es_vip:
            print("🔄 Reintentando con modelo estándar...")
            imagen_url, error_fal = crear_con_fal(prompt_mejorado, formato, False)
        
        # 🔄 CLOUDFLARE (Respaldo)
        if not imagen_url:
            print(f"⚠️ Motor principal falló: {error_fal}")
            print("🔄 Usando motor secundario...")
            imagen_url, error_cf = crear_con_cloudflare(prompt_mejorado, width, height)
            
            if not imagen_url and error_cf and "400" in str(error_cf):
                imagen_url, error_cf = crear_con_cloudflare(prompt_mejorado, width, height)
        
        # 🥉 POLLINATIONS (Último respaldo)
        if not imagen_url:
            print("🔄 Usando motor de respaldo...")
            imagen_url, error_pol = generar_con_pollinations(prompt_mejorado, width, height)
            
            if not imagen_url:
                return jsonify({
                    'error': 'Servicio temporalmente no disponible',
                    'message': 'Intenta en 1 minuto',
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
            'proveedor': proveedor_publico,
            'formato': formato,
            'es_vip': es_vip,
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

        # 🥇 FAL.AI IMAGE-TO-IMAGE (Principal)
        imagen_url, error_fal = editar_con_fal(prompt, imagen_input)

        # 🔄 CLOUDFLARE (Respaldo)
        if not imagen_url:
            print(f"⚠️ Motor premium falló: {error_fal}")
            print("🔄 Usando motor secundario...")
            imagen_url, error_cf = editar_con_cloudflare(prompt, imagen_input)

            if not imagen_url and error_cf and "400" in str(error_cf):
                imagen_url, error_cf = editar_con_cloudflare(prompt, imagen_input)

            if not imagen_url:
                return jsonify({
                    'error': 'No se pudo editar la imagen',
                    'message': 'Intenta con otra descripción',
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
        'version': 'V6.1 - Didasko AI + Fal.ai FLUX',
        'motor_principal_configurado': bool(FAL_API_KEY),
        'motor_secundario_configurado': bool(CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN),
        'usuario_logueado': session.get('usuario_id') is not None,
        'creado_por': 'Didasko AI',
        'modelos': {
            'crear_free': 'FLUX.1-schnell',
            'crear_vip': 'FLUX.1-dev',
            'editar': 'FLUX image-to-image'
        }
    })
