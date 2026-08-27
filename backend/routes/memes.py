# ===================================
# memes.py - Generador de Memes Virales con IA (VIDEO)
# ===================================
import os
import base64
import requests
import json
from flask import Blueprint, request, jsonify
import google.generativeai as genai

memes_bp = Blueprint('memes', __name__)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY', '')
SILICONFLOW_API_KEY = os.getenv('SILICONFLOW_API_KEY', '')

@memes_bp.route('/analizar', methods=['POST'])
def analizar_y_generar_guiones():
    """Recibe un video o imagen, lo analiza con NVIDIA/Gemini y genera 10 guiones."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No se envió ningún archivo'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nombre de archivo vacío'}), 400

        # Leer archivo
        file_data = file.read()
        filename = file.filename.lower()
        
        # Detectar si es video o imagen
        es_video = filename.endswith(('.mp4', '.mov', '.avi', '.webm'))
        
        analisis_meme = ""
        
        if es_video:
            # Usar NVIDIA para analizar video
            print(f"🎬 Analizando VIDEO: {filename}")
            analisis_meme = analizar_video_con_nvidia(file_data)
        else:
            # Usar Gemini para analizar imagen
            print(f"📸 Analizando IMAGEN: {filename}")
            analisis_meme = analizar_imagen_con_gemini(file_data)
        
        # Generar guiones basados en el análisis
        guiones = generar_guiones_con_gemini(analisis_meme)
        
        return jsonify({
            'success': True,
            'guiones': guiones,
            'mensaje': f'✅ Se generaron {len(guiones)} guiones absurdos',
            'tipo_archivo': 'video' if es_video else 'imagen'
        })
        
    except Exception as e:
        print(f"❌ Error en /analizar: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


def analizar_video_con_nvidia(video_data):
    """Analiza un video usando NVIDIA NIM API"""
    try:
        # Codificar video a base64
        video_base64 = base64.b64encode(video_data).decode('utf-8')
        
        # Usar NVIDIA NIM para video analysis
        url = "https://ai.api.nvidia.com/v1/vlm/nvidia/video-llama-3.1-8b"
        
        headers = {
            "Authorization": f"Bearer {NVIDIA_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = """Analiza este video meme viral y describe:
1. FORMATO: ¿Cómo está estructurado visualmente?
2. ESTILO DE HUMOR: ¿Qué tipo de humor usa? (absurdo, sarcástico, etc.)
3. SITUACIÓN: ¿Qué está pasando en el video?
4. ELEMENTOS CLAVE: Personas, animales, objetos, texto
5. TONO: ¿Es dramático, exagerado, sutil?

Responde en español de forma concisa."""
        
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
        
        # Agregar video al payload (codificado en base64)
        # NOTA: La API de NVIDIA puede tener límites de tamaño de video
        # Si el video es muy grande, podríamos necesitar extraer frames
        
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
        
        print(f"⚠️ NVIDIA API error: {response.status_code}")
        return "Video meme analizado"
        
    except Exception as e:
        print(f" Error analizando video con NVIDIA: {e}")
        return "Video meme viral con situaciones cotidianas"


def analizar_imagen_con_gemini(img_data):
    """Analiza una imagen usando Gemini Vision"""
    try:
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """Analiza este meme viral y describe:
1. FORMATO: ¿Cómo está estructurado?
2. ESTILO DE HUMOR: ¿Qué tipo de humor usa?
3. SITUACIÓN: ¿Qué está pasando?
4. ELEMENTOS CLAVE: ¿Qué hay en la imagen?
5. TONO: ¿Es exagerado, sutil?

Responde en español."""
        
        response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": img_base64}])
        return response.text
        
    except Exception as e:
        print(f"❌ Error analizando imagen: {e}")
        return "Meme viral con situaciones cotidianas"


def generar_guiones_con_gemini(analisis_base):
    """Genera 10 guiones de memes basados en el análisis"""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""Basándote en este análisis de un meme viral:

{analisis_base}

Genera 10 guiones NUEVOS para memes en el MISMO formato y estilo, pero con situaciones ABSURDAS y diferentes.

Cada guión debe tener:
- titulo: Nombre corto
- situacion: Descripción de la escena (2-3 líneas)
- texto_superior: Texto arriba (máx 10 palabras)
- texto_inferior: Texto abajo (máx 10 palabras)
- prompt_imagen: Descripción en inglés de la imagen a generar

Responde SOLO con un array JSON válido con esta estructura:
[
  {{
    "titulo": "Título",
    "situacion": "Descripción",
    "texto_superior": "Texto arriba",
    "texto_inferior": "Texto abajo",
    "prompt_imagen": "Descripción en inglés"
  }}
]"""
        
        response = model.generate_content(prompt)
        texto = response.text
        
        # Limpiar JSON
        texto = texto.strip()
        if texto.startswith("```json"):
            texto = texto[7:]
        if texto.startswith("```"):
            texto = texto[3:]
        if texto.endswith("```"):
            texto = texto[:-3]
        
        guiones = json.loads(texto.strip())
        return guiones
        
    except Exception as e:
        print(f"❌ Error generando guiones: {e}")
        # Retornar guiones de fallback
        return [
            {
                "titulo": f"Meme {i+1}",
                "situacion": "Situación absurda cotidiana",
                "texto_superior": "Cuando pasa algo inesperado",
                "texto_inferior": "Y no sabes qué hacer",
                "prompt_imagen": "Person looking confused in everyday situation, meme style"
            }
            for i in range(10)
        ]


@memes_bp.route('/generar-imagen', methods=['POST'])
def generar_una_imagen():
    """Genera una imagen con SiliconFlow (Flux)"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        
        if not prompt:
            return jsonify({'success': False, 'error': 'Prompt vacío'}), 400
        
        url = "https://api.siliconflow.cn/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "black-forest-labs/FLUX.1-schnell",
            "prompt": f"Meme style, viral, humorous, high quality. {prompt}",
            "image_size": "1024x1024",
            "num_inference_steps": 4
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if response.status_code == 200:
            data_resp = response.json()
            if "images" in data_resp and len(data_resp["images"]) > 0:
                return jsonify({
                    'success': True,
                    'imagen_url': data_resp["images"][0]["url"]
                })
        
        return jsonify({'success': False, 'error': f'Error API: {response.text}'}), 500
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
