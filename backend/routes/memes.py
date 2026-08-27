# ===================================
# memes.py - Generador de Memes Virales
# Versión: 3.0 - NVIDIA (análisis) + Fal.ai (imágenes)
# ===================================
# - Qwen2.5-VL-72B (NVIDIA): Análisis de imagen/video - GRATIS
# - Fal.ai: Generación de imágenes - TUS CRÉDITOS PAGADOS
# ===================================

import os
import base64
import requests
import json
from flask import Blueprint, request, jsonify

memes_bp = Blueprint('memes', __name__)

# ===================================
# CONFIGURACIÓN DE APIS
# ===================================
NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY', '')
FAL_API_KEY = os.getenv('FAL_API_KEY', '')

# Endpoints
NVIDIA_VISION_URL = "https://ai.api.nvidia.com/v1/gr/qwen/qwen2.5-vl-72b-instruct"
FAL_API_URL = "https://api.fal.ai/models"

# ===================================
# ENDPOINT PRINCIPAL: ANALIZAR MEME
# ===================================
@memes_bp.route('/analizar', methods=['POST'])
def analizar_y_generar_guiones():
    """Recibe un video o imagen, lo analiza con Qwen-VL y genera 10 guiones."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No se envió ningún archivo'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nombre de archivo vacío'}), 400

        file_data = file.read()
        filename = file.filename.lower()
        file_size_mb = len(file_data) / (1024 * 1024)
        
        print(f"\n{'='*60}")
        print(f"📁 Archivo recibido: {filename}")
        print(f" Tamaño: {file_size_mb:.2f} MB")
        
        es_video = filename.endswith(('.mp4', '.mov', '.avi', '.webm', '.mkv'))
        
        # Analizar con Qwen-VL
        print(" Analizando con Qwen2.5-VL-72B (NVIDIA)...")
        analisis_meme = analizar_con_qwen_vl(file_data, es_video)
        
        print(f"\n Análisis obtenido:")
        print(f"{'-'*60}")
        print(analisis_meme[:300] + "..." if len(analisis_meme) > 300 else analisis_meme)
        print(f"{'-'*60}\n")
        
        # Generar 10 guiones
        print(" Generando 10 guiones absurdos con Qwen...")
        guiones = generar_guiones_con_qwen(analisis_meme)
        
        print(f"✅ {len(guiones)} guiones generados exitosamente")
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': True,
            'guiones': guiones,
            'mensaje': f'✅ Se generaron {len(guiones)} guiones absurdos',
            'tipo_archivo': 'video' if es_video else 'imagen'
        })
        
    except Exception as e:
        print(f"❌ Error en /analizar: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ===================================
# FUNCIÓN: ANALIZAR CON QWEN-VL
# ===================================
def analizar_con_qwen_vl(file_data, es_video):
    """Analiza imagen o video usando Qwen2.5-VL-72B de NVIDIA"""
    try:
        file_base64 = base64.b64encode(file_data).decode('utf-8')
        
        mime_type = "video/mp4" if es_video else "image/jpeg"
        
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = """Analiza este meme viral en detalle:

1. FORMATO VISUAL: ¿Cómo está estructurado?
2. ESTILO DE HUMOR: ¿Qué tipo de humor usa?
3. SITUACIÓN: ¿Qué está pasando?
4. ELEMENTOS CLAVE: Personas, animales, objetos, expresiones
5. TONO: ¿Es exagerado, sutil, caótico?

Responde en español de forma concisa."""

        payload = {
            "model": "qwen/qwen2.5-vl-72b-instruct",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{file_base64}"}}
                    ]
                }
            ],
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        print(f"📡 Enviando a NVIDIA Qwen-VL ({'video' if es_video else 'imagen'})...")
        response = requests.post(NVIDIA_VISION_URL, json=payload, headers=headers, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                contenido = data["choices"][0]["message"]["content"]
                print("✅ Análisis completado con Qwen-VL")
                return contenido
            else:
                print(f"⚠️ Respuesta sin contenido: {data}")
                return "Meme viral con situaciones cotidianas y humor"
        else:
            print(f" NVIDIA API error {response.status_code}: {response.text[:200]}")
            return "Meme viral con situaciones cotidianas"
        
    except Exception as e:
        print(f"❌ Error analizando con Qwen-VL: {str(e)}")
        return "Meme viral con humor"


# ===================================
# FUNCIÓN: GENERAR GUIONES CON QWEN
# ===================================
def generar_guiones_con_qwen(analisis_base):
    """Genera 10 guiones usando Qwen-VL"""
    try:
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Basándote en este análisis:

{analisis_base}

Genera EXACTAMENTE 10 guiones NUEVOS para memes en el MISMO formato y estilo, 
pero con situaciones ABSURDAS y EXAGERADAS.

REGLAS:
- Mantén el mismo formato visual
- Usa humor ABSURDO
- Textos CORTOS (máx 10 palabras)
- Situaciones RELATABLES pero RIDÍCULAS
- Varía los temas

Responde SOLO con JSON array:

[
  {{
    "titulo": "Cuando tu jefe te pide horas extra",
    "situacion": "Persona mirando el reloj con cara de desesperación",
    "texto_superior": "Cuando son las 5:59 PM",
    "texto_inferior": "Y tu jefe dice 'necesito hablar contigo'",
    "prompt_imagen": "Office worker looking at clock horrified, boss approaching, meme style"
  }}
]

¡Genera 10 guiones variados!"""

        payload = {
            "model": "qwen/qwen2.5-vl-72b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2048,
            "temperature": 0.8,
            "top_p": 0.9
        }
        
        print("📡 Enviando a Qwen para generar guiones...")
        response = requests.post(NVIDIA_VISION_URL, json=payload, headers=headers, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                texto = data["choices"][0]["message"]["content"]
                
                # Limpiar JSON
                texto = texto.strip()
                if texto.startswith("```json"):
                    texto = texto[7:]
                if texto.startswith("```"):
                    texto = texto[3:]
                if texto.endswith("```"):
                    texto = texto[:-3]
                
                guiones = json.loads(texto.strip())
                print(f"✅ {len(guiones)} guiones generados")
                return guiones
        
        print(f"⚠️ Error generando guiones: {response.status_code}")
        return generar_guiones_fallback()
        
    except json.JSONDecodeError as e:
        print(f"❌ Error JSON: {str(e)}")
        return generar_guiones_fallback()
    except Exception as e:
        print(f"❌ Error generando guiones: {str(e)}")
        return generar_guiones_fallback()


def generar_guiones_fallback():
    """Guiones de fallback"""
    print("⚠️ Usando guiones de fallback")
    return [
        {
            "titulo": "Cuando todo sale mal",
            "situacion": "Persona frustrada mirando el caos",
            "texto_superior": "Cuando intentas hacer algo simple",
            "texto_inferior": "Y todo sale terriblemente mal",
            "prompt_imagen": "Person looking extremely frustrated surrounded by chaos, meme style, humorous"
        },
        {
            "titulo": "Lunes por la mañana",
            "situacion": "Persona arrastrándose fuera de la cama",
            "texto_superior": "Lunes 6:00 AM",
            "texto_inferior": "Mi cara recordando que existe el trabajo",
            "prompt_imagen": "Exhausted person crawling out of bed, zombie-like, Monday morning meme"
        },
        {
            "titulo": "Mi billetera",
            "situacion": "Billetera vacía con una polilla",
            "texto_superior": "Yo después de pagar cuentas",
            "texto_inferior": "¿Qué es esto de comer?",
            "prompt_imagen": "Empty wallet with moth flying out, broke meme, humorous"
        },
        {
            "titulo": "Cuando alguien me saluda",
            "situacion": "Persona fingiendo no ver",
            "texto_superior": "Cuando veo a alguien que conozco",
            "texto_inferior": "Pero no tengo ganas de hablar",
            "prompt_imagen": "Person pretending not to see someone, awkward avoidance meme"
        },
        {
            "titulo": "Mi productividad",
            "situacion": "Persona trabajando 5 minutos y distrayéndose",
            "texto_superior": "Yo: Voy a ser productivo hoy",
            "texto_inferior": "También yo: *ve un meme*",
            "prompt_imagen": "Person distracted by phone instead of working, procrastination meme"
        },
        {
            "titulo": "Cuando llega el viernes",
            "situacion": "Persona celebrando exageradamente",
            "texto_superior": "Viernes 5:00 PM",
            "texto_inferior": "Modo fin de semana: ACTIVADO",
            "prompt_imagen": "Person celebrating Friday afternoon, excited expression, meme"
        },
        {
            "titulo": "Mi dieta",
            "situacion": "Persona comiendo pizza a las 3 AM",
            "texto_superior": "Yo: El lunes empiezo la dieta",
            "texto_inferior": "Yo el domingo a las 11 PM:",
            "prompt_imagen": "Person eating junk food late at night, diet starting Monday meme"
        },
        {
            "titulo": "Trabajo en equipo",
            "situacion": "Persona trabajando sola",
            "texto_superior": "Trabajo en equipo:",
            "texto_inferior": "Yo trabajando, ellos en el nombre",
            "prompt_imagen": "One person doing all work in group project, frustrated meme"
        },
        {
            "titulo": "Mi cuenta bancaria",
            "situacion": "Persona mirando su cuenta con horror",
            "texto_superior": "Yo revisando mi cuenta después del fin de semana",
            "texto_inferior": "¿En qué gasté todo?",
            "prompt_imagen": "Person shocked looking at bank account, broke meme"
        },
        {
            "titulo": "Modo concentración",
            "situacion": "Persona con cara de molestia",
            "texto_superior": "Yo en modo concentración:",
            "texto_inferior": "*alguien respira fuerte*",
            "prompt_imagen": "Person with annoyed expression when someone makes noise, focus meme"
        }
    ]


# ===================================
# ENDPOINT: GENERAR IMAGEN (FAL.AI)
# ===================================
@memes_bp.route('/generar-imagen', methods=['POST'])
def generar_una_imagen():
    """Genera imagen usando Fal.ai (tus créditos pagados)"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        
        if not prompt:
            return jsonify({'success': False, 'error': 'Prompt vacío'}), 400
        
        print(f"\n🎨 Generando imagen con Fal.ai...")
        print(f"Prompt: {prompt[:100]}...")
        
        # Fal.ai - Usar Flux (mejor calidad) o Stable Diffusion
        # Endpoint: https://api.fal.ai/models/{model_id}
        model_id = "fal-ai/flux/dev"  # o "fal-ai/stable-diffusion-v3-medium"
        
        url = f"{FAL_API_URL}/{model_id}"
        
        headers = {
            "Authorization": f"Key {FAL_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Mejorar prompt para estilo meme
        enhanced_prompt = f"""meme style, viral, humorous, high quality, realistic lighting, 
        exaggerated expressions, internet meme aesthetic, professional photography. {prompt}"""
        
        payload = {
            "prompt": enhanced_prompt,
            "image_size": {
                "width": 1024,
                "height": 1024
            },
            "num_inference_steps": 28,
            "guidance_scale": 3.5
        }
        
        print(f"📡 Enviando solicitud a Fal.ai ({model_id})...")
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if response.status_code == 200:
            data_resp = response.json()
            
            # Fal.ai devuelve la imagen en "images" array
            if "images" in data_resp and len(data_resp["images"]) > 0:
                image_url = data_resp["images"][0]["url"]
                print(f"✅ Imagen generada exitosamente: {image_url[:80]}...")
                
                return jsonify({
                    'success': True,
                    'imagen_url': image_url
                })
            else:
                print(f"⚠️ Sin imagen en respuesta: {data_resp}")
                return jsonify({
                    'success': False, 
                    'error': 'Fal.ai no devolvió imagen'
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
    """Test del módulo"""
    return jsonify({
        'status': 'ok',
        'module': 'memes',
        'version': '3.0 - NVIDIA + Fal.ai',
        'apis_configured': {
            'nvidia': bool(NVIDIA_API_KEY),
            'fal_ai': bool(FAL_API_KEY)
        },
        'features': [
            'Análisis de imagen/video con Qwen2.5-VL-72B (NVIDIA - GRATIS)',
            'Generación de guiones con Qwen',
            'Generación de imágenes con Fal.ai (CRÉDITOS PAGADOS)'
        ]
    })
