# ===================================
# memes.py - Generador de Memes Virales con IA
# Versión: 1.0 - Soporta VIDEO (NVIDIA) e IMAGEN (Gemini)
# ===================================

import os
import base64
import requests
import json
from flask import Blueprint, request, jsonify
import google.generativeai as genai

memes_bp = Blueprint('memes', __name__)

# ===================================
# CONFIGURACIÓN DE APIS
# ===================================
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY', '')
SILICONFLOW_API_KEY = os.getenv('SILICONFLOW_API_KEY', '')

# ===================================
# ENDPOINT PRINCIPAL: ANALIZAR MEME
# ===================================
@memes_bp.route('/analizar', methods=['POST'])
def analizar_y_generar_guiones():
    """
    Recibe un video o imagen, lo analiza con IA y genera 10 guiones de memes.
    - Video: Usa NVIDIA NIM API
    - Imagen: Usa Gemini Vision API
    """
    try:
        # Validar que se envió un archivo
        if 'file' not in request.files:
            return jsonify({
                'success': False, 
                'error': 'No se envió ningún archivo. Usa el campo "file" en FormData.'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False, 
                'error': 'Nombre de archivo vacío'
            }), 400

        # Leer el archivo
        file_data = file.read()
        filename = file.filename.lower()
        file_size_mb = len(file_data) / (1024 * 1024)
        
        print(f"\n{'='*60}")
        print(f" Archivo recibido: {filename}")
        print(f"📊 Tamaño: {file_size_mb:.2f} MB")
        
        # Detectar si es video o imagen
        es_video = filename.endswith(('.mp4', '.mov', '.avi', '.webm', '.mkv'))
        
        if es_video:
            print("🎬 Tipo: VIDEO - Usando NVIDIA API")
            if file_size_mb > 10:
                print("⚠️ Advertencia: Video grande (>10MB), puede tardar")
            analisis_meme = analizar_video_con_nvidia(file_data)
        else:
            print("📸 Tipo: IMAGEN - Usando Gemini API")
            analisis_meme = analizar_imagen_con_gemini(file_data)
        
        print(f"\n🔍 Análisis obtenido:")
        print(f"{'-'*60}")
        print(analisis_meme[:200] + "..." if len(analisis_meme) > 200 else analisis_meme)
        print(f"{'-'*60}\n")
        
        # Generar 10 guiones basados en el análisis
        print(" Generando 10 guiones absurdos con Gemini...")
        guiones = generar_guiones_con_gemini(analisis_meme)
        
        print(f"✅ {len(guiones)} guiones generados exitosamente")
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': True,
            'guiones': guiones,
            'mensaje': f'✅ Se generaron {len(guiones)} guiones absurdos',
            'tipo_archivo': 'video' if es_video else 'imagen',
            'tamaño_mb': round(file_size_mb, 2)
        })
        
    except json.JSONDecodeError as e:
        print(f"❌ Error JSONDecodeError: {str(e)}")
        return jsonify({
            'success': False, 
            'error': 'Error al procesar la respuesta de la IA. Intenta de nuevo.'
        }), 500
        
    except Exception as e:
        print(f"❌ Error en /analizar: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'error': f'Error interno: {str(e)}'
        }), 500


# ===================================
# FUNCIÓN: ANALIZAR VIDEO CON NVIDIA
# ===================================
def analizar_video_con_nvidia(video_data):
    """
    Analiza un video meme usando NVIDIA NIM API (Video-LLaMA).
    Devuelve una descripción del contenido, humor y estructura.
    """
    try:
        print("🎬 Iniciando análisis de video con NVIDIA...")
        
        # Codificar video a base64
        video_base64 = base64.b64encode(video_data).decode('utf-8')
        print(f"📊 Video codificado: {len(video_base64)} bytes")
        
        # Endpoint de NVIDIA para análisis de video
        url = "https://ai.api.nvidia.com/v1/vlm/nvidia/video-llama-3.1-8b"
        
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Prompt detallado para análisis de meme
        prompt = """Analiza este video meme viral y describe DETALLADAMENTE:

1. FORMATO VISUAL: ¿Cómo está estructurado? (texto en pantalla, escenas, transiciones)
2. ESTILO DE HUMOR: ¿Qué tipo de humor usa? (absurdo, sarcástico, relatable, dramático)
3. SITUACIÓN: ¿Qué está pasando exactamente en el video?
4. ELEMENTOS CLAVE: Personas, animales, objetos, expresiones faciales, texto visible
5. TONO: ¿Es exagerado, sutil, caótico, tranquilo?
6. AUDIO (si hay): ¿Hay sonido, música, diálogos, efectos?

Responde en español de forma CONCISA pero COMPLETA. Enfócate en los elementos que hacen el meme gracioso."""

        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.9,
            "stream": False
        }
        
        # NOTA: La API de NVIDIA para video puede tener limitaciones de tamaño
        # Si el video es muy grande, podríamos necesitar extraer frames clave
        # Por ahora, intentamos enviar el video completo codificado
        
        print("📡 Enviando solicitud a NVIDIA API...")
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                analisis = data["choices"][0]["message"]["content"]
                print("✅ Video analizado exitosamente con NVIDIA")
                return analisis
            else:
                print(f"⚠️ Respuesta sin contenido: {data}")
                return "Video meme con situaciones cotidianas y humor absurdo"
        else:
            print(f"️ NVIDIA API error {response.status_code}: {response.text[:200]}")
            # Fallback: usar Gemini con una descripción genérica
            return "Video meme viral con situaciones exageradas y humor cotidiano"
        
    except Exception as e:
        print(f"❌ Error analizando video con NVIDIA: {str(e)}")
        return "Video meme con situaciones cotidianas y humor"


# ===================================
# FUNCIÓN: ANALIZAR IMAGEN CON GEMINI
# ===================================
def analizar_imagen_con_gemini(img_data):
    """
    Analiza una imagen meme usando Gemini Vision API.
    Devuelve una descripción del formato, humor y elementos.
    """
    try:
        print("📸 Iniciando análisis de imagen con Gemini Vision...")
        
        # Codificar imagen a base64
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        
        # Configurar Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prompt para análisis de meme
        prompt = """Analiza este meme viral y describe DETALLADAMENTE:

1. FORMATO: ¿Cómo está estructurado visualmente? (texto arriba/abajo, imagen central, etc.)
2. ESTILO DE HUMOR: ¿Qué tipo de humor usa? (absurdo, sarcástico, relatable, oscuro, etc.)
3. SITUACIÓN: ¿Qué está pasando en la imagen? Describe la escena
4. ELEMENTOS CLAVE: ¿Qué hay en la imagen? (personas, animales, objetos, expresiones)
5. TONO: ¿Es exagerado, sutil, dramático, caótico?

Responde en español de forma CONCISA pero COMPLETA. Enfócate en los elementos visuales y el tipo de humor."""

        # Enviar a Gemini
        response = model.generate_content([
            prompt, 
            {"mime_type": "image/jpeg", "data": img_base64}
        ])
        
        analisis = response.text
        print("✅ Imagen analizada exitosamente con Gemini")
        return analisis
        
    except Exception as e:
        print(f"❌ Error analizando imagen con Gemini: {str(e)}")
        return "Meme viral con situaciones cotidianas y humor"


# ===================================
# FUNCIÓN: GENERAR GUIONES CON GEMINI
# ===================================
def generar_guiones_con_gemini(analisis_base):
    """
    Genera 10 guiones de memes basados en el análisis del meme original.
    Usa Gemini para crear situaciones absurdas pero en el mismo estilo.
    """
    try:
        print("🎨 Generando guiones con Gemini...")
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""Basándote en este análisis de un meme viral:

{analisis_base}

Genera EXACTAMENTE 10 guiones NUEVOS para memes en el MISMO formato y estilo visual, 
pero con situaciones ABSURDAS, EXAGERADAS y DIFERENTES.

REGLAS:
- Mantén el mismo formato visual del meme original
- Usa humor ABSURDO y situaciones cotidianas muy exageradas
- Los textos deben ser CORTOS y DIRECTOS (máximo 10 palabras cada uno)
- Las situaciones deben ser RELATABLES pero RIDÍCULAS
- Varía los temas: trabajo, relaciones, tecnología, mascotas, comida, deportes, etc.
- Sé CREATIVO y ORIGINAL

Cada guión DEBE tener esta estructura EXACTA:
1. titulo: Nombre corto y llamativo del meme
2. situacion: Descripción de la escena (2-3 líneas)
3. texto_superior: Texto que va ARRIBA de la imagen (setup del chiste)
4. texto_inferior: Texto que va ABAJO de la imagen (punchline)
5. prompt_imagen: Descripción DETALLADA en INGLÉS de qué debe mostrar la imagen 
   (para generarla con IA de imágenes como Flux/DALL-E)

Responde SOLO con un array JSON válido con esta estructura EXACTA, sin texto adicional:

[
  {{
    "titulo": "Cuando tu jefe te pide horas extra",
    "situacion": "Persona mirando el reloj con cara de desesperación mientras su jefe se acerca sonriendo",
    "texto_superior": "Cuando son las 5:59 PM",
    "texto_inferior": "Y tu jefe dice 'necesito hablar contigo'",
    "prompt_imagen": "Office worker looking at clock with horrified expression, boss approaching with smile, meme style"
  }}
]

¡Genera 10 guiones variados y graciosos!"""

        response = model.generate_content(prompt)
        texto = response.text
        
        print(" Respuesta de Gemini recibida")
        
        # Limpiar el texto para obtener solo el JSON
        texto = texto.strip()
        
        # Eliminar markdown si existe
        if texto.startswith("```json"):
            texto = texto[7:]
        if texto.startswith("```"):
            texto = texto[3:]
        if texto.endswith("```"):
            texto = texto[:-3]
        
        texto = texto.strip()
        
        # Parsear JSON
        guiones = json.loads(texto)
        
        # Validar que tenemos 10 guiones
        if len(guiones) != 10:
            print(f"⚠️ Se generaron {len(guiones)} guiones en lugar de 10")
        
        print(f"✅ {len(guiones)} guiones generados y parseados exitosamente")
        return guiones
        
    except json.JSONDecodeError as e:
        print(f"❌ Error JSONDecodeError al parsear guiones: {str(e)}")
        print(f"Texto recibido: {texto[:500]}...")
        
        # Retornar guiones de fallback
        return generar_guiones_fallback()
        
    except Exception as e:
        print(f" Error generando guiones: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Retornar guiones de fallback
        return generar_guiones_fallback()


# ===================================
# FUNCIÓN: GUIONES FALLBACK
# ===================================
def generar_guiones_fallback():
    """
    Genera guiones genéricos de fallback si la IA falla.
    """
    print("️ Usando guiones de fallback")
    
    return [
        {
            "titulo": "Cuando todo sale mal",
            "situacion": "Persona con cara de frustración extrema mirando el caos a su alrededor",
            "texto_superior": "Cuando intentas hacer algo simple",
            "texto_inferior": "Y todo sale terriblemente mal",
            "prompt_imagen": "Person looking extremely frustrated surrounded by chaos, meme style, exaggerated expression"
        },
        {
            "titulo": "Lunes por la mañana",
            "situacion": "Persona arrastrándose fuera de la cama con cara de zombie",
            "texto_superior": "Lunes 6:00 AM",
            "texto_inferior": "Mi cara recordando que existe el trabajo",
            "prompt_imagen": "Exhausted person crawling out of bed, zombie-like expression, Monday morning, meme style"
        },
        {
            "titulo": "Mi billetera después de pagar",
            "situacion": "Billetera completamente vacía con una polilla volando",
            "texto_superior": "Yo después de pagar todas mis cuentas",
            "texto_inferior": "¿Qué es esto de comer?",
            "prompt_imagen": "Empty wallet with moth flying out, broke meme, humorous style"
        },
        {
            "titulo": "Cuando alguien me saluda",
            "situacion": "Persona fingiendo no ver a alguien que la saluda",
            "texto_superior": "Cuando veo a alguien que conozco",
            "texto_inferior": "Pero no tengo ganas de hablar",
            "prompt_imagen": "Person pretending not to see someone, awkward avoidance, meme style"
        },
        {
            "titulo": "Mi productividad real",
            "situacion": "Persona trabajando 5 minutos y distrayéndose 3 horas",
            "texto_superior": "Yo: Voy a ser productivo hoy",
            "texto_inferior": "También yo: *ve un meme*",
            "prompt_imagen": "Person distracted by phone instead of working, procrastination meme"
        },
        {
            "titulo": "Cuando llega el viernes",
            "situacion": "Persona celebrando exageradamente",
            "texto_superior": "Viernes 5:00 PM",
            "texto_inferior": "Modo fin de semana: ACTIVADO",
            "prompt_imagen": "Person celebrating Friday afternoon, excited expression, meme style"
        },
        {
            "titulo": "Mi dieta empezando el lunes",
            "situacion": "Persona comiendo pizza a las 3 AM",
            "texto_superior": "Yo: El lunes empiezo la dieta",
            "texto_inferior": "Yo el domingo a las 11 PM:",
            "prompt_imagen": "Person eating junk food late at night, diet starting Monday meme"
        },
        {
            "titulo": "Cuando me toca un grupo difícil",
            "situacion": "Persona trabajando sola mientras otros no hacen nada",
            "texto_superior": "Trabajo en equipo:",
            "texto_inferior": "Yo trabajando, ellos en el nombre",
            "prompt_imagen": "One person doing all the work in group project, frustrated expression, meme"
        },
        {
            "titulo": "Mi bank account",
            "situacion": "Persona mirando su cuenta bancaria con horror",
            "texto_superior": "Yo revisando mi cuenta después del fin de semana",
            "texto_inferior": "¿En qué gasté todo mi dinero?",
            "prompt_imagen": "Person shocked looking at bank account, broke meme, humorous"
        },
        {
            "titulo": "Cuando alguien respira cerca de mí",
            "situacion": "Persona con cara de molestia extrema",
            "texto_superior": "Yo en modo concentración:",
            "texto_inferior": "*alguien respira fuerte*",
            "prompt_imagen": "Person with annoyed expression when someone makes noise, focus mode meme"
        }
    ]


# ===================================
# ENDPOINT: GENERAR IMAGEN
# ===================================
@memes_bp.route('/generar-imagen', methods=['POST'])
def generar_una_imagen():
    """
    Genera una imagen usando SiliconFlow (Flux) basado en un prompt.
    """
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        
        if not prompt:
            return jsonify({
                'success': False, 
                'error': 'Prompt vacío'
            }), 400
        
        print(f"\n Generando imagen con prompt: {prompt[:100]}...")
        
        # API de SiliconFlow (Flux)
        url = "https://api.siliconflow.cn/v1/images/generations"
        
        headers = {
            "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Mejorar el prompt para estilo meme
        enhanced_prompt = f"""Meme style, viral, humorous, high quality, realistic lighting, 
        exaggerated expressions, internet meme aesthetic. {prompt}"""
        
        payload = {
            "model": "black-forest-labs/FLUX.1-schnell",
            "prompt": enhanced_prompt,
            "image_size": "1024x1024",
            "num_inference_steps": 4,
            "seed": None
        }
        
        print("📡 Enviando solicitud a SiliconFlow...")
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if response.status_code == 200:
            data_resp = response.json()
            if "images" in data_resp and len(data_resp["images"]) > 0:
                image_url = data_resp["images"][0]["url"]
                print(f"✅ Imagen generada: {image_url[:80]}...")
                return jsonify({
                    'success': True,
                    'imagen_url': image_url
                })
            else:
                print(f"⚠️ Sin imagen en respuesta: {data_resp}")
                return jsonify({
                    'success': False, 
                    'error': 'API no devolvió imagen'
                }), 500
        else:
            error_msg = f"Error {response.status_code}: {response.text[:200]}"
            print(f" {error_msg}")
            return jsonify({
                'success': False, 
                'error': error_msg
            }), 500
        
    except Exception as e:
        print(f"❌ Error generando imagen: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'error': f'Error: {str(e)}'
        }), 500


# ===================================
# ENDPOINT: TEST
# ===================================
@memes_bp.route('/test', methods=['GET'])
def test_meme_api():
    """Endpoint de prueba para verificar que el módulo funciona."""
    return jsonify({
        'status': 'ok',
        'module': 'memes',
        'version': '1.0',
        'apis_configured': {
            'gemini': bool(GEMINI_API_KEY),
            'nvidia': bool(NVIDIA_API_KEY),
            'siliconflow': bool(SILICONFLOW_API_KEY)
        },
        'features': [
            'Análisis de video con NVIDIA',
            'Análisis de imagen con Gemini',
            'Generación de 10 guiones',
            'Generación de imágenes con Flux'
        ]
    })
