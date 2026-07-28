# ===================================
# vision.py - Endpoint de Análisis de Fotos
# ===================================
# Usa NVIDIA Vision (principal) + Gemini Vision (respaldo)
# Resuelve tareas fotografiadas
# ===================================

import os
import base64
from io import BytesIO
from flask import Blueprint, request, jsonify
from openai import OpenAI
import google.generativeai as genai
from PIL import Image

# Crear Blueprint para las rutas de visión
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
# Instrucción del sistema para análisis
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
    """Convierte imagen PIL a string base64 (JPEG)"""
    buffer = BytesIO()
    imagen_pil.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

# ===================================
# Análisis con NVIDIA
# ===================================

def analizar_con_nvidia(imagen_pil, prompt):
    """Analiza imagen usando NVIDIA Vision"""
    imagen_b64 = pil_a_base64(imagen_pil)

    response = nvidia_client.chat.completions.create(
        model="nvidia/nemotron-nano-12b-v2-vl",
        messages=[
            {
                "role": "system",
                "content": VISION_INSTRUCTION
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{imagen_b64}"
                        }
                    }
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
    """Analiza imagen usando Gemini Vision"""
    model = genai.GenerativeModel(
        model_name='gemini-flash-latest',
        system_instruction=VISION_INSTRUCTION
    )
    response = model.generate_content([prompt, imagen_pil])
    return response.text

# ===================================
# Endpoint principal de análisis
# ===================================

@vision_bp.route('/analizar', methods=['POST'])
def analizar_imagen():
    """
    Recibe una imagen y una descripción de qué hacer con ella.
    """
    try:
        if not NVIDIA_API_KEY and not GEMINI_API_KEY:
            return jsonify({
                'error': 'Sin API configurada',
                'message': 'Configura NVIDIA_API_KEY o GEMINI_API_KEY'
            }), 500

        imagen_pil = None
        prompt = ""

        # OPCIÓN 1: Recibe archivo directo (form-data)
        if 'imagen' in request.files:
            archivo = request.files['imagen']

            if archivo.filename == '':
                return jsonify({
                    'error': 'No se seleccionó archivo',
                    'message': 'Selecciona una imagen para analizar'
                }), 400

            imagen_pil = Image.open(archivo.stream)
            prompt = request.form.get('prompt', '').strip()

        # OPCIÓN 2: Recibe imagen en base64 (JSON)
        elif request.is_json:
            data = request.get_json()
            imagen_base64 = data.get('imagen_base64', '')
            prompt = data.get('prompt', '').strip()

            if not imagen_base64:
                return jsonify({
                    'error': 'Falta imagen',
                    'message': 'Envía una imagen para analizar'
                }), 400

            if ',' in imagen_base64:
                imagen_base64 = imagen_base64.split(',')[1]

            imagen_bytes = base64.b64decode(imagen_base64)
            imagen_pil = Image.open(BytesIO(imagen_bytes))

        else:
            return jsonify({
                'error': 'Formato inválido',
                'message': 'Envía la imagen como archivo o base64'
            }), 400

        if not prompt:
            prompt = "Analiza esta imagen y ayúdame con lo que ves. Explica paso a paso."

        # Convertir a RGB si es necesario
        if imagen_pil.mode != 'RGB':
            imagen_pil = imagen_pil.convert('RGB')

        # Intentar con NVIDIA primero
        respuesta_texto = None
        modelo_usado = "none"

        if nvidia_client:
            try:
                respuesta_texto = analizar_con_nvidia(imagen_pil, prompt)
                modelo_usado = "nvidia"
            except Exception as e:
                print(f"⚠️ NVIDIA Vision falló: {e} — usando Gemini como respaldo")

        # Si NVIDIA falla, usar Gemini
        if not respuesta_texto and GEMINI_API_KEY:
            try:
                respuesta_texto = analizar_con_gemini(imagen_pil, prompt)
                modelo_usado = "gemini"
            except Exception as e:
                print(f"❌ Gemini Vision también falló: {e}")
                return jsonify({
                    'error': 'Error en ambos servicios',
                    'message': str(e),
                    'success': False
                }), 500

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
# Endpoint de prueba
# ===================================

@vision_bp.route('/test', methods=['GET'])
def test():
    """Verifica que el endpoint de visión está funcionando"""
    return jsonify({
        'status': 'ok',
        'endpoint': 'vision',
        'nvidia_configurado': bool(NVIDIA_API_KEY),
        'gemini_configurado': bool(GEMINI_API_KEY),
        'message': '🔍 Vision endpoint funcionando'
    })
