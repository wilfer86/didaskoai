# ===================================
# memes.py - Generador de Memes Virales con IA
# Versión: 1.1 - Usa Hugging Face para imágenes
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
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')

# ===================================
# ENDPOINT PRINCIPAL: ANALIZAR MEME
# ===================================
@memes_bp.route('/analizar', methods=['POST'])
def analizar_y_generar_guiones():
    """Recibe un video o imagen, lo analiza con IA y genera 10 guiones."""
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
        print(f"📊 Tamaño: {file_size_mb:.2f} MB")
        
        es_video = filename.endswith(('.mp4', '.mov', '.avi', '.webm', '.mkv'))
        
        if es_video:
            print("🎬 Tipo: VIDEO - Usando NVIDIA API")
            analisis_meme = analizar_video_con_nvidia(file_data)
        else:
            print("📸 Tipo: IMAGEN - Usando Gemini API")
            analisis_meme = analizar_imagen_con_gemini(file_data)
        
        print(f"\n🔍 Análisis obtenido:")
        print(f"{'-'*60}")
        print(analisis_meme[:200] + "..." if len(analisis_meme) > 200 else analisis_meme)
        print(f"{'-'*60}\n")
        
        print("🎨 Generando 10 guiones absurdos con Gemini...")
        guiones = generar_guiones_con_gemini(analisis_meme)
        
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
        return jsonify({'success': False, 'error': str(e)}), 500


# ===================================
# FUNCIÓN: ANALIZAR VIDEO CON NVIDIA
# ===================================
def analizar_video_con_nvidia(video_data):
    """Analiza video usando NVIDIA NIM API"""
    try:
        print("🎬 Iniciando análisis de video con NVIDIA...")
        video_base64 = base64.b64encode(video_data).decode('utf-8')
        
        url = "https://ai.api.nvidia.com/v1/vlm/nvidia/video-llama-3.1-8b"
        
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = """Analiza este video meme viral y describe:
1. FORMATO VISUAL
2. ESTILO DE HUMOR
3. SITUACIÓN
4. ELEMENTOS CLAVE
5. TONO

Responde en español."""

        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.9,
            "stream": False
        }
        
        print("📡 Enviando solicitud a NVIDIA API...")
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                print("✅ Video analizado con NVIDIA")
                return data["choices"][0]["message"]["content"]
        
        print(f"⚠️ NVIDIA API error: {response.status_code}")
        return "Video meme con situaciones cotidianas"
        
    except Exception as e:
        print(f"❌ Error analizando video: {str(e)}")
        return "Video meme viral"


# ===================================
# FUNCIÓN: ANALIZAR IMAGEN CON GEMINI
# ===================================
def analizar_imagen_con_gemini(img_data):
    """Analiza imagen usando Gemini Vision"""
    try:
        print("📸 Iniciando análisis con Gemini Vision...")
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """Analiza este meme viral:
1. FORMATO
2. ESTILO DE HUMOR
3. SITUACIÓN
4. ELEMENTOS CLAVE
5. TONO

Responde en español."""

        response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": img_base64}])
        print("✅ Imagen analizada con Gemini")
        return response.text
        
    except Exception as e:
        print(f"❌ Error analizando imagen: {str(e)}")
        return "Meme viral con situaciones cotidianas"


# ===================================
# FUNCIÓN: GENERAR GUIONES CON GEMINI
# ===================================
def generar_guiones_con_gemini(analisis_base):
    """Genera 10 guiones basados en el análisis"""
    try:
        print("🎨 Generando guiones con Gemini...")
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""Basándote en este análisis:

{analisis_base}

Genera 10 guiones NUEVOS con situaciones ABSURDAS.

Cada guión debe tener:
- titulo
- situacion
- texto_superior
- texto_inferior
- prompt_imagen (descripción en inglés)

Responde SOLO con JSON array:

[
  {{
    "titulo": "Título",
    "situacion": "Descripción",
    "texto_superior": "Texto arriba",
    "texto_inferior": "Texto abajo",
    "prompt_imagen": "English description"
  }}
]"""

        response = model.generate_content(prompt)
        texto = response.text
        
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
        
    except Exception as e:
        print(f"❌ Error generando guiones: {str(e)}")
        return generar_guiones_fallback()


def generar_guiones_fallback():
    """Guiones de fallback"""
    return [
        {
            "titulo": "Cuando todo sale mal",
            "situacion": "Persona frustrada mirando el caos",
            "texto_superior": "Cuando intentas hacer algo simple",
            "texto_inferior": "Y todo sale mal",
            "prompt_imagen": "Person looking frustrated surrounded by chaos, meme style"
        }
        for i in range(10)
    ]


# ===================================
# ENDPOINT: GENERAR IMAGEN (HUGGING FACE)
# ===================================
@memes_bp.route('/generar-imagen', methods=['POST'])
def generar_una_imagen():
    """Genera imagen usando Hugging Face Inference API"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        
        if not prompt:
            return jsonify({'success': False, 'error': 'Prompt vacío'}), 400
        
        print(f"\n🎨 Generando imagen con Hugging Face...")
        print(f"Prompt: {prompt[:100]}...")
        
        # Usar Hugging Face Inference API con Stable Diffusion
        API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        
        headers = {
            "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Mejorar prompt para meme
        enhanced_prompt = f"""meme style, viral, humorous, high quality, {prompt}"""
        
        payload = {
            "inputs": enhanced_prompt,
            "parameters": {
                "width": 1024,
                "height": 1024,
                "num_inference_steps": 30
            }
        }
        
        print("📡 Enviando solicitud a Hugging Face...")
        response = requests.post(API_URL, json=payload, headers=headers, timeout=60)
        
        if response.status_code == 200:
            # Hugging Face devuelve la imagen en binario
            # Necesitamos subirla a un servicio o devolverla como base64
            import base64
            from io import BytesIO
            
            image_data = response.content
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Crear URL de datos base64
            image_url = f"data:image/png;base64,{image_base64}"
            
            print(f"✅ Imagen generada exitosamente ({len(image_data)} bytes)")
            
            return jsonify({
                'success': True,
                'imagen_url': image_url
            })
        else:
            error_msg = f"Error {response.status_code}: {response.text[:200]}"
            print(f"❌ {error_msg}")
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
        'version': '1.1 - Hugging Face',
        'apis_configured': {
            'gemini': bool(GEMINI_API_KEY),
            'nvidia': bool(NVIDIA_API_KEY),
            'huggingface': bool(HUGGINGFACE_API_KEY)
        }
    })
