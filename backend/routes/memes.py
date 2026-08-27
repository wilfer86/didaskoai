# ===================================
# memes.py - Generador de Memes Virales con IA
# ===================================
import os
import base64
import requests
import json
from flask import Blueprint, request, jsonify
import google.generativeai as genai

memes_bp = Blueprint('memes', __name__)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
SILICONFLOW_API_KEY = os.getenv('SILICONFLOW_API_KEY', '')

@memes_bp.route('/analizar', methods=['POST'])
def analizar_y_generar_guiones():
    """Recibe una imagen, la analiza con Gemini y genera 10 guiones de memes."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No se envió ningún archivo'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nombre de archivo vacío'}), 400

        # Leer y codificar imagen
        img_data = file.read()
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        
        # Configurar Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """Analiza este meme viral y genera 10 guiones NUEVOS con situaciones ABSURDAS pero en el MISMO formato y estilo visual.

Responde SOLO con un array JSON válido con esta estructura exacta, sin texto adicional:
[
  {
    "titulo": "Nombre corto",
    "situacion": "Descripción de la escena (2-3 líneas)",
    "texto_superior": "Texto arriba (máx 10 palabras)",
    "texto_inferior": "Texto abajo (máx 10 palabras)",
    "prompt_imagen": "Descripción en inglés de lo que debe mostrar la imagen para generarla con IA"
  }
]"""

        response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": img_base64}])
        texto_respuesta = response.text
        
        # Limpiar la respuesta para asegurar que sea JSON válido
        texto_limpio = texto_respuesta.strip()
        if texto_limpio.startswith("```json"):
            texto_limpio = texto_limpio[7:]
        if texto_limpio.startswith("```"):
            texto_limpio = texto_limpio[3:]
        if texto_limpio.endswith("```"):
            texto_limpio = texto_limpio[:-3]
            
        guiones = json.loads(texto_limpio.strip())
        
        return jsonify({
            'success': True,
            'guiones': guiones,
            'mensaje': f'✅ Se generaron {len(guiones)} guiones absurdos'
        })
        
    except json.JSONDecodeError:
        return jsonify({'success': False, 'error': 'La IA no devolvió un JSON válido. Intenta de nuevo.'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@memes_bp.route('/generar-imagen', methods=['POST'])
def generar_una_imagen():
    """Recibe un prompt y genera una imagen con SiliconFlow (Flux)."""
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
            "prompt": f"Meme style, viral, humorous, high quality, realistic lighting. {prompt}",
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
