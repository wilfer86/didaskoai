# ===================================
# vision.py - Endpoint de Análisis de Fotos V3.2
# ===================================
# NVIDIA Vision (principal) + Gemini Vision (respaldo)
# 🆕 Sube imágenes a Supabase Storage
# 🔧 FIX: Historial vincula imagen correcta al análisis
# ===================================

import os
import base64
from io import BytesIO
from flask import Blueprint, request, jsonify, session
from openai import OpenAI
import google.generativeai as genai
from PIL import Image
from supabase_client import guardar_chat, get_client, subir_imagen_storage

vision_bp = Blueprint('vision', __name__)

# ===================================
# Configurar NVIDIA (principal)
# ===================================

NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY')

nvidia_client = None
if NVIDIA_API_KEY:
    nvidia_client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=NVIDIA_API_KEY
    )

# ===================================
# Configurar Gemini (respaldo)
# ===================================

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ===================================
# Instrucción del sistema
# ===================================

VISION_INSTRUCTION = """
Eres Didasko AI 🦉, un tutor educativo que analiza imágenes académicas.

TU TAREA:
Analizar la imagen que te envía el estudiante y ayudarle según lo que pida.

TIPOS DE IMÁGENES QUE PUEDES ANALIZAR:
📐 Ejercicios de matemáticas (ecuaciones, geometría, cálculos)
📝 Textos, párrafos, preguntas
🧪 Diagramas científicos, fórmulas químicas
🗺️ Mapas, gráficos, tablas
🎨 Dibujos, diagramas
📚 Páginas de libros, hojas de tareas
📊 Ejercicios de cualquier materia

CÓMO RESPONDER:
1. Primero describe brevemente qué ves en la imagen
2. Luego resuelve o explica lo que el usuario pidió
3. Muestra el PROCESO paso a paso (no solo la respuesta)
4. Adapta el nivel según lo que veas (primaria/secundaria/universidad)
5. Usa formato claro con emojis, listas y subtítulos

SI EL USUARIO NO ESPECIFICA QUÉ QUIERE:
Ofrece opciones: "Puedo ayudarte a: resolver el ejercicio, explicar el tema, corregir errores..."

REGLAS:
- SIEMPRE muestra el proceso educativo
- Si la imagen es de un examen, guía SIN dar respuestas directas
- Si la imagen no es clara, pide una foto mejor
- Responde en español
- Sé motivador al final
"""

# ===================================
# Función auxiliar: PIL → base64
# ===================================

def pil_a_base64(imagen_pil):
    buffer = BytesIO()
    imagen_pil.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

# ===================================
# 🆕 Guardar análisis en Supabase (con vínculo perfecto)
# ===================================
def guardar_analisis_vision(usuario_id, prompt, respuesta, imagen_url_publica, modelo):
    """Guarda el análisis con vínculo directo imagen ↔ chat."""
    try:
        client = get_client()
        if not client:
            return
        
        # 🔧 PRIMERO guardar la imagen y obtener su ID
        imagen_id = None
        if imagen_url_publica:
            try:
                res_img = client.table('imagenes').insert({
                    'usuario_id': usuario_id,
                    'url': imagen_url_publica,
                    'prompt': prompt[:500],
                    'formato': 'original',
                    'tipo': 'analizada'
                }).execute()
                if res_img.data:
                    imagen_id = res_img.data[0]['id']
                    print(f"✅ Imagen guardada con ID: {imagen_id}")
            except Exception as e:
                print(f"⚠️ Error guardando imagen: {e}")
        
        # 🔧 LUEGO guardar el chat con referencia a la imagen
        # Usamos modelo_usado para guardar el imagen_id (formato: "nvidia|IMG_ID")
        modelo_con_ref = f"{modelo}|{imagen_id}" if imagen_id else modelo
        
        client.table('chats').insert({
            'usuario_id': usuario_id,
            'seccion': 'vision',
            'mensaje_usuario': prompt,
            'respuesta_ia': respuesta,
            'modelo_usado': modelo_con_ref
        }).execute()
        
        print(f"✅ Análisis vision guardado con vínculo")
    except Exception as e:
        print(f"⚠️ No se guardó análisis: {e}")

# ===================================
# Análisis con NVIDIA
# ===================================

def analizar_con_nvidia(imagen_pil, prompt):
    imagen_b64 = pil_a_base64(imagen_pil)

    response = nvidia_client.chat.completions.create(
        model="nvidia/nemotron-nano-12b-v2-vl",
        messages=[
            {"role": "system", "content": VISION_INSTRUCTION},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{imagen_b64}"}}
                ]
            }
        ],
        temperature=0.7,
        max_tokens=1500
    )
    return response.choices[0].message.content

# ===================================
# Análisis con Gemini (respaldo)
# ===================================

def analizar_con_gemini(imagen_pil, prompt):
    model = genai.GenerativeModel(
        model_name='gemini-flash-latest',
        system_instruction=VISION_INSTRUCTION
    )
    response = model.generate_content([prompt, imagen_pil])
    return response.text

# ===================================
# Endpoint principal
# ===================================

@vision_bp.route('/analizar', methods=['POST'])
def analizar_imagen():
    try:
        if not NVIDIA_API_KEY and not GEMINI_API_KEY:
            return jsonify({
                'error': 'Sin API configurada'
            }), 500

        imagen_pil = None
        prompt = ""
        imagen_base64_original = None

        # OPCIÓN 1: archivo (form-data)
        if 'imagen' in request.files:
            archivo = request.files['imagen']
            if archivo.filename == '':
                return jsonify({'error': 'No se seleccionó archivo'}), 400

            imagen_pil = Image.open(archivo.stream)
            prompt = request.form.get('prompt', '').strip()
            buffer = BytesIO()
            imagen_pil.save(buffer, format="JPEG", quality=85)
            imagen_base64_original = f"data:image/jpeg;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"

        # OPCIÓN 2: base64 (JSON)
        elif request.is_json:
            data = request.get_json()
            imagen_base64 = data.get('imagen_base64', '')
            prompt = data.get('prompt', '').strip()

            if not imagen_base64:
                return jsonify({'error': 'Falta imagen'}), 400

            imagen_base64_original = imagen_base64

            if ',' in imagen_base64:
                imagen_base64 = imagen_base64.split(',')[1]

            imagen_bytes = base64.b64decode(imagen_base64)
            imagen_pil = Image.open(BytesIO(imagen_bytes))
        else:
            return jsonify({'error': 'Formato inválido'}), 400

        if not prompt:
            prompt = "Analiza esta imagen y ayúdame con lo que ves. Explica paso a paso."

        if imagen_pil.mode != 'RGB':
            imagen_pil = imagen_pil.convert('RGB')

        usuario_id = session.get('usuario_id')

        # NVIDIA primero
        respuesta_texto = None
        modelo_usado = "none"

        if nvidia_client:
            try:
                respuesta_texto = analizar_con_nvidia(imagen_pil, prompt)
                modelo_usado = "nvidia"
            except Exception as e:
                print(f"⚠️ NVIDIA Vision falló: {e} — usando Gemini")

        # Gemini como respaldo
        if not respuesta_texto and GEMINI_API_KEY:
            try:
                respuesta_texto = analizar_con_gemini(imagen_pil, prompt)
                modelo_usado = "gemini"
            except Exception as e:
                return jsonify({
                    'error': 'Error en ambos servicios',
                    'message': str(e),
                    'success': False
                }), 500

        # 🆕 Subir imagen a Storage y guardar análisis
        if usuario_id and respuesta_texto:
            print("📤 Subiendo imagen analizada a Storage...")
            url_publica = subir_imagen_storage(imagen_base64_original, usuario_id, 'analizada')
            guardar_analisis_vision(
                usuario_id=usuario_id,
                prompt=prompt,
                respuesta=respuesta_texto,
                imagen_url_publica=url_publica,
                modelo=modelo_usado
            )

        return jsonify({
            'respuesta': respuesta_texto,
            'prompt_usado': prompt,
            'modelo': modelo_usado,
            'success': True
        })

    except Exception as e:
        return jsonify({
            'error': 'Error al analizar imagen',
            'message': str(e),
            'success': False
        }), 500

# ===================================
# 🔧 Endpoint HISTORIAL - CORREGIDO
# ===================================

@vision_bp.route('/historial', methods=['GET'])
def obtener_historial_vision():
    """Devuelve los análisis de fotos con vínculo directo a imagen."""
    try:
        usuario_id = session.get('usuario_id')
        if not usuario_id:
            return jsonify({'success': False, 'error': 'Sin sesión'}), 401

        client = get_client()
        limite = int(request.args.get('limite', 20))

        # Obtener chats de vision
        chats = client.table('chats').select('*').eq('usuario_id', usuario_id).eq('seccion', 'vision').order('fecha', desc=True).limit(limite).execute()

        analisis = []
        for chat in chats.data:
            imagen_url = None
            modelo_raw = chat.get('modelo_usado', '')
            
            # 🔧 NUEVO: Extraer imagen_id del campo modelo_usado
            if '|' in modelo_raw:
                partes = modelo_raw.split('|')
                modelo = partes[0]
                imagen_id = partes[1] if len(partes) > 1 else None
                
                # Buscar la imagen exacta por ID
                if imagen_id and imagen_id != 'None':
                    try:
                        img_res = client.table('imagenes').select('url').eq('id', imagen_id).execute()
                        if img_res.data:
                            imagen_url = img_res.data[0]['url']
                    except:
                        pass
            else:
                modelo = modelo_raw
            
            # 🔧 FALLBACK: Si no hay vínculo, buscar por prompt exacto (análisis viejos)
            if not imagen_url:
                try:
                    prompt_completo = chat['mensaje_usuario'][:500]
                    fecha_chat = chat['fecha']
                    
                    img_res = client.table('imagenes').select('url').eq('usuario_id', usuario_id).eq('tipo', 'analizada').eq('prompt', prompt_completo).order('fecha', desc=True).limit(1).execute()
                    if img_res.data:
                        imagen_url = img_res.data[0]['url']
                except:
                    pass
            
            analisis.append({
                'id': chat['id'],
                'prompt': chat['mensaje_usuario'],
                'respuesta': chat['respuesta_ia'],
                'imagen_url': imagen_url,
                'fecha': chat['fecha'],
                'modelo': modelo
            })

        return jsonify({
            'success': True,
            'total': len(analisis),
            'analisis': analisis
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===================================
# 🆕 Endpoint: ELIMINAR análisis
# ===================================

@vision_bp.route('/eliminar/<analisis_id>', methods=['DELETE'])
def eliminar_analisis(analisis_id):
    try:
        usuario_id = session.get('usuario_id')
        if not usuario_id:
            return jsonify({'success': False, 'error': 'Sin sesión'}), 401

        client = get_client()
        
        # Obtener imagen_id del chat para eliminar también la imagen
        chat_res = client.table('chats').select('modelo_usado').eq('id', analisis_id).execute()
        if chat_res.data:
            modelo_raw = chat_res.data[0].get('modelo_usado', '')
            if '|' in modelo_raw:
                imagen_id = modelo_raw.split('|')[1]
                if imagen_id and imagen_id != 'None':
                    try:
                        client.table('imagenes').delete().eq('id', imagen_id).eq('usuario_id', usuario_id).execute()
                    except:
                        pass
        
        client.table('chats').delete().eq('id', analisis_id).eq('usuario_id', usuario_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===================================
# Endpoint de prueba
# ===================================

@vision_bp.route('/test', methods=['GET'])
def test():
    return jsonify({
        'status': 'ok',
        'endpoint': 'vision',
        'nvidia_configurado': bool(NVIDIA_API_KEY),
        'gemini_configurado': bool(GEMINI_API_KEY),
        'usuario_logueado': session.get('usuario_id') is not None,
        'message': '🔍 Vision endpoint V3.2 - vínculo directo imagen ↔ chat'
    })
